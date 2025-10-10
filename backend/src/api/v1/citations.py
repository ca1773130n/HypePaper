"""Citations API routes (Citation graph operations).

Endpoints:
- GET /api/v1/citations/graph - Multi-level citation graph traversal
- POST /api/v1/citations/discover - Citation-based paper discovery
- GET /api/v1/citations/stats - Citation statistics
"""
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ...models import Paper, PaperReference
from .dependencies import get_db

router = APIRouter(prefix="/api/v1/citations", tags=["citations"])


# Request/Response models
class GraphNode(BaseModel):
    """Citation graph node (paper)."""

    paper_id: str
    title: str
    authors: Optional[list[str]] = None
    year: Optional[int] = None
    venue: Optional[str] = None
    citations_in_count: int
    citations_out_count: int
    level: int
    arxiv_id: Optional[str] = None
    doi: Optional[str] = None


class GraphEdge(BaseModel):
    """Citation graph edge (citation relationship)."""

    source_id: str
    target_id: str
    relationship: str  # "cites" or "cited_by"
    reference_text: Optional[str] = None
    match_score: Optional[float] = None
    match_method: Optional[str] = None
    verified: bool = False


class CitationGraph(BaseModel):
    """Citation graph response."""

    root_paper_id: str
    root_paper_title: str
    depth: int
    direction: str
    total_nodes: int
    total_edges: int
    nodes: list[GraphNode]
    edges: list[GraphEdge]
    metadata: Optional[dict] = None


class DiscoveryRequest(BaseModel):
    """Citation discovery request."""

    seed_paper_id: str
    strategies: list[str] = Field(
        default=["citing_papers", "cited_papers"],
        description="Discovery strategies to apply"
    )
    max_papers_per_strategy: int = Field(
        default=20,
        ge=1,
        le=100,
        description="Max papers per strategy"
    )
    filters: Optional[dict] = None


class DiscoveredPaper(BaseModel):
    """Discovered paper info."""

    paper_id: str
    title: str
    authors: list[str]
    year: Optional[int] = None
    venue: Optional[str] = None
    citations_count: int
    relevance_score: float


class DiscoveryStrategyResult(BaseModel):
    """Discovery results for a single strategy."""

    strategy: str
    count: int
    papers: list[DiscoveredPaper]


class DiscoveryResponse(BaseModel):
    """Citation discovery response."""

    seed_paper_id: str
    seed_paper_title: str
    strategies_applied: list[str]
    total_discovered: int
    papers: list[DiscoveryStrategyResult]
    metadata: Optional[dict] = None


class CitationStats(BaseModel):
    """Citation statistics response."""

    metric: str
    paper_id: Optional[str] = None
    data: dict


@router.get("/graph", response_model=CitationGraph)
async def get_citation_graph(
    paper_id: str = Query(..., description="Root paper UUID or ArXiv ID"),
    depth: int = Query(2, ge=1, le=3, description="Traversal depth"),
    direction: str = Query("both", regex="^(in|out|both)$", description="Traversal direction"),
    min_match_score: float = Query(70.0, ge=0, le=100, description="Minimum fuzzy match score"),
    max_nodes: int = Query(500, ge=1, le=1000, description="Maximum nodes to return"),
    db: AsyncSession = Depends(get_db),
) -> CitationGraph:
    """Get citation graph with multi-level traversal.

    Builds a citation network starting from a root paper, traversing citations
    up to the specified depth.
    """
    import time
    start_time = time.time()

    # Get root paper
    try:
        paper_uuid = UUID(paper_id)
        query = select(Paper).where(Paper.id == paper_uuid)
    except ValueError:
        query = select(Paper).where(Paper.arxiv_id == paper_id)

    result = await db.execute(query)
    root_paper = result.scalar_one_or_none()

    if not root_paper:
        raise HTTPException(status_code=404, detail="Root paper not found")

    # Track visited papers and build graph
    visited_papers = {root_paper.id}
    nodes = []
    edges = []

    # Add root node
    root_in_count_query = select(func.count()).where(PaperReference.reference_id == root_paper.id)
    root_out_count_query = select(func.count()).where(PaperReference.paper_id == root_paper.id)

    root_in_count = (await db.execute(root_in_count_query)).scalar() or 0
    root_out_count = (await db.execute(root_out_count_query)).scalar() or 0

    nodes.append(
        GraphNode(
            paper_id=str(root_paper.id),
            title=root_paper.title,
            authors=root_paper.authors,
            year=root_paper.year,
            venue=root_paper.venue,
            citations_in_count=root_in_count,
            citations_out_count=root_out_count,
            level=0,
            arxiv_id=root_paper.arxiv_id,
            doi=root_paper.doi,
        )
    )

    # BFS traversal
    current_level = [root_paper.id]

    for level in range(1, depth + 1):
        if len(nodes) >= max_nodes:
            break

        next_level = []

        for current_paper_id in current_level:
            # Get citations based on direction
            citation_queries = []

            if direction in ["in", "both"]:
                # Papers citing current paper
                citation_queries.append(
                    select(PaperReference)
                    .where(
                        and_(
                            PaperReference.reference_id == current_paper_id,
                            or_(
                                PaperReference.match_score.is_(None),
                                PaperReference.match_score >= min_match_score,
                            ),
                        )
                    )
                    .options(selectinload(PaperReference.paper))
                )

            if direction in ["out", "both"]:
                # Papers cited by current paper
                citation_queries.append(
                    select(PaperReference)
                    .where(
                        and_(
                            PaperReference.paper_id == current_paper_id,
                            or_(
                                PaperReference.match_score.is_(None),
                                PaperReference.match_score >= min_match_score,
                            ),
                        )
                    )
                    .options(selectinload(PaperReference.referenced_paper))
                )

            for citation_query in citation_queries:
                citation_result = await db.execute(citation_query)
                citations = list(citation_result.scalars().all())

                for citation in citations:
                    # Determine which paper is the related one
                    if citation.paper_id == current_paper_id:
                        # Outgoing citation
                        related_paper = citation.referenced_paper
                        edge_relationship = "cites"
                        source_id = str(current_paper_id)
                        target_id = str(related_paper.id)
                    else:
                        # Incoming citation
                        related_paper = citation.paper
                        edge_relationship = "cited_by"
                        source_id = str(related_paper.id)
                        target_id = str(current_paper_id)

                    # Skip if already visited or max nodes reached
                    if related_paper.id in visited_papers or len(nodes) >= max_nodes:
                        continue

                    visited_papers.add(related_paper.id)
                    next_level.append(related_paper.id)

                    # Get citation counts for related paper
                    in_count_query = select(func.count()).where(PaperReference.reference_id == related_paper.id)
                    out_count_query = select(func.count()).where(PaperReference.paper_id == related_paper.id)

                    in_count = (await db.execute(in_count_query)).scalar() or 0
                    out_count = (await db.execute(out_count_query)).scalar() or 0

                    # Add node
                    nodes.append(
                        GraphNode(
                            paper_id=str(related_paper.id),
                            title=related_paper.title,
                            authors=related_paper.authors,
                            year=related_paper.year,
                            venue=related_paper.venue,
                            citations_in_count=in_count,
                            citations_out_count=out_count,
                            level=level,
                            arxiv_id=related_paper.arxiv_id,
                            doi=related_paper.doi,
                        )
                    )

                    # Add edge
                    edges.append(
                        GraphEdge(
                            source_id=source_id,
                            target_id=target_id,
                            relationship=edge_relationship,
                            reference_text=citation.reference_text,
                            match_score=citation.match_score,
                            match_method=citation.match_method,
                            verified=citation.verified_at is not None,
                        )
                    )

        current_level = next_level

    query_time_ms = int((time.time() - start_time) * 1000)

    return CitationGraph(
        root_paper_id=str(root_paper.id),
        root_paper_title=root_paper.title,
        depth=depth,
        direction=direction,
        total_nodes=len(nodes),
        total_edges=len(edges),
        nodes=nodes,
        edges=edges,
        metadata={
            "query_time_ms": query_time_ms,
            "truncated": len(nodes) >= max_nodes,
        },
    )


@router.post("/discover", response_model=DiscoveryResponse)
async def discover_via_citations(
    request: DiscoveryRequest,
    db: AsyncSession = Depends(get_db),
) -> DiscoveryResponse:
    """Discover papers through citation network traversal.

    Uses multiple strategies to find related papers based on citation relationships.
    """
    import time
    start_time = time.time()

    # Get seed paper
    try:
        paper_uuid = UUID(request.seed_paper_id)
        query = select(Paper).where(Paper.id == paper_uuid)
    except ValueError:
        query = select(Paper).where(Paper.arxiv_id == request.seed_paper_id)

    result = await db.execute(query)
    seed_paper = result.scalar_one_or_none()

    if not seed_paper:
        raise HTTPException(status_code=404, detail="Seed paper not found")

    strategy_results = []
    total_discovered = 0

    # Apply each strategy
    for strategy in request.strategies:
        papers = []

        if strategy == "citing_papers":
            # Papers that cite the seed paper
            citing_query = (
                select(Paper)
                .join(PaperReference, PaperReference.paper_id == Paper.id)
                .where(PaperReference.reference_id == seed_paper.id)
                .limit(request.max_papers_per_strategy)
            )
            citing_result = await db.execute(citing_query)
            citing_papers = list(citing_result.scalars().all())

            for paper in citing_papers:
                in_count = len(paper.citations_in) if hasattr(paper, 'citations_in') else 0
                papers.append(
                    DiscoveredPaper(
                        paper_id=str(paper.id),
                        title=paper.title,
                        authors=paper.authors,
                        year=paper.year,
                        venue=paper.venue,
                        citations_count=in_count,
                        relevance_score=0.9,  # High relevance for direct citations
                    )
                )

        elif strategy == "cited_papers":
            # Papers cited by the seed paper
            cited_query = (
                select(Paper)
                .join(PaperReference, PaperReference.reference_id == Paper.id)
                .where(PaperReference.paper_id == seed_paper.id)
                .limit(request.max_papers_per_strategy)
            )
            cited_result = await db.execute(cited_query)
            cited_papers = list(cited_result.scalars().all())

            for paper in cited_papers:
                in_count = len(paper.citations_in) if hasattr(paper, 'citations_in') else 0
                papers.append(
                    DiscoveredPaper(
                        paper_id=str(paper.id),
                        title=paper.title,
                        authors=paper.authors,
                        year=paper.year,
                        venue=paper.venue,
                        citations_count=in_count,
                        relevance_score=0.85,  # High relevance for references
                    )
                )

        elif strategy == "co_cited_papers":
            # Papers co-cited with seed paper (cited by same papers)
            # This is a more complex query - simplified version
            cocited_query = (
                select(Paper)
                .join(PaperReference, PaperReference.reference_id == Paper.id)
                .where(
                    and_(
                        Paper.id != seed_paper.id,
                        PaperReference.paper_id.in_(
                            select(PaperReference.paper_id)
                            .where(PaperReference.reference_id == seed_paper.id)
                        ),
                    )
                )
                .limit(request.max_papers_per_strategy)
            )
            cocited_result = await db.execute(cocited_query)
            cocited_papers = list(cocited_result.scalars().all())

            for paper in cocited_papers:
                in_count = len(paper.citations_in) if hasattr(paper, 'citations_in') else 0
                papers.append(
                    DiscoveredPaper(
                        paper_id=str(paper.id),
                        title=paper.title,
                        authors=paper.authors,
                        year=paper.year,
                        venue=paper.venue,
                        citations_count=in_count,
                        relevance_score=0.75,  # Medium relevance for co-citations
                    )
                )

        elif strategy == "same_author_papers":
            # Papers by the same authors
            author_papers = []
            for author in seed_paper.authors[:3]:  # Limit to first 3 authors
                author_query = (
                    select(Paper)
                    .where(
                        and_(
                            Paper.id != seed_paper.id,
                            Paper.authors.contains([author]),
                        )
                    )
                    .limit(request.max_papers_per_strategy // 3)
                )
                author_result = await db.execute(author_query)
                author_papers.extend(list(author_result.scalars().all()))

            for paper in author_papers[:request.max_papers_per_strategy]:
                in_count = len(paper.citations_in) if hasattr(paper, 'citations_in') else 0
                papers.append(
                    DiscoveredPaper(
                        paper_id=str(paper.id),
                        title=paper.title,
                        authors=paper.authors,
                        year=paper.year,
                        venue=paper.venue,
                        citations_count=in_count,
                        relevance_score=0.7,  # Medium relevance for same author
                    )
                )

        # Apply filters if specified
        if request.filters:
            if "min_year" in request.filters:
                papers = [p for p in papers if p.year and p.year >= request.filters["min_year"]]
            if "max_year" in request.filters:
                papers = [p for p in papers if p.year and p.year <= request.filters["max_year"]]
            if "venues" in request.filters and request.filters["venues"]:
                papers = [p for p in papers if p.venue in request.filters["venues"]]
            if "min_citations" in request.filters:
                papers = [p for p in papers if p.citations_count >= request.filters["min_citations"]]

        strategy_results.append(
            DiscoveryStrategyResult(
                strategy=strategy,
                count=len(papers),
                papers=papers,
            )
        )
        total_discovered += len(papers)

    query_time_ms = int((time.time() - start_time) * 1000)

    return DiscoveryResponse(
        seed_paper_id=str(seed_paper.id),
        seed_paper_title=seed_paper.title,
        strategies_applied=request.strategies,
        total_discovered=total_discovered,
        papers=strategy_results,
        metadata={
            "query_time_ms": query_time_ms,
            "filters_applied": request.filters,
        },
    )


@router.get("/stats", response_model=CitationStats)
async def get_citation_stats(
    paper_id: Optional[str] = Query(None, description="Paper UUID (omit for corpus-wide)"),
    metric: str = Query(
        "distribution",
        regex="^(distribution|top_citing|velocity|co_citation)$",
        description="Statistic to compute"
    ),
    limit: int = Query(10, ge=1, le=100, description="Limit for top-N results"),
    db: AsyncSession = Depends(get_db),
) -> CitationStats:
    """Get citation statistics for a paper or corpus.

    Computes various citation metrics including distribution, top citing papers,
    citation velocity, and co-citation analysis.
    """
    data = {}

    if paper_id:
        # Paper-specific stats
        try:
            paper_uuid = UUID(paper_id)
            query = select(Paper).where(Paper.id == paper_uuid)
        except ValueError:
            query = select(Paper).where(Paper.arxiv_id == paper_id)

        result = await db.execute(query)
        paper = result.scalar_one_or_none()

        if not paper:
            raise HTTPException(status_code=404, detail="Paper not found")

        if metric == "distribution":
            # Citation count distribution
            total_query = select(func.count()).where(PaperReference.reference_id == paper.id)
            total = (await db.execute(total_query)).scalar() or 0

            data = {
                "total_citations": total,
                "paper_id": str(paper.id),
                "paper_title": paper.title,
            }

        elif metric == "top_citing":
            # Top papers citing this paper
            top_query = (
                select(Paper)
                .join(PaperReference, PaperReference.paper_id == Paper.id)
                .where(PaperReference.reference_id == paper.id)
                .limit(limit)
            )
            top_result = await db.execute(top_query)
            top_papers = list(top_result.scalars().all())

            data = {
                "paper_id": str(paper.id),
                "top_citing_papers": [
                    {
                        "paper_id": str(p.id),
                        "title": p.title,
                        "authors": p.authors,
                        "year": p.year,
                    }
                    for p in top_papers
                ],
            }

        elif metric == "velocity":
            # Citation velocity over time (citations per year)
            # This is a simplified version - would need temporal data
            data = {
                "paper_id": str(paper.id),
                "message": "Citation velocity requires temporal citation data (not yet implemented)",
            }

        elif metric == "co_citation":
            # Papers frequently co-cited with this paper
            data = {
                "paper_id": str(paper.id),
                "message": "Co-citation analysis requires complex graph queries (not yet implemented)",
            }

    else:
        # Corpus-wide stats
        if metric == "distribution":
            # Overall citation distribution
            total_papers_query = select(func.count()).select_from(Paper)
            total_citations_query = select(func.count()).select_from(PaperReference)

            total_papers = (await db.execute(total_papers_query)).scalar() or 0
            total_citations = (await db.execute(total_citations_query)).scalar() or 0

            avg_citations = total_citations / total_papers if total_papers > 0 else 0

            data = {
                "total_papers": total_papers,
                "total_citations": total_citations,
                "average_citations_per_paper": round(avg_citations, 2),
            }

    return CitationStats(
        metric=metric,
        paper_id=paper_id,
        data=data,
    )
