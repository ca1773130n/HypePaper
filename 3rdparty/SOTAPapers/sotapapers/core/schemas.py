from pydantic import BaseModel
from typing import Optional, List, Dict
from enum import Enum

from sotapapers.utils.id_util import detect_arxiv_id_from_citation

class PaperType(str, Enum):
    UNKNOWN = "unknown"
    JOURNAL_PAPER = "journal_paper"
    CONFERENCE_PAPER = "conference_paper"
    BOOK = "book"
    BOOK_CHAPTER = "book_chapter"
    REPORT = "report"
    ARXIV_PAPER = "arxiv_paper"

class PaperSessionType(str, Enum):
    UNKNOWN = "unknown"
    ORAL = "oral"
    POSTER = "poster"

class PaperAcceptStatus(str, Enum):
    UNKNOWN = "unknown"
    BEST_PAPER_AWARD = "best_paper_award"
    AWARD_CANDIDATE = "award_candidate"
    HILIGHTED = "highlighted"
    NORMAL = "normal"

class PaperComparison(str, Enum):
    UNKNOWN = "unknown"
    OUTSTANDING = "outstanding"
    EVEN_BETTER = "even_better"
    BETTER = "better"
    SIMILAR = "similar"
    NOT_THAT_GOOD = "not_that_good"
    
class PaperContent(BaseModel):
    abstract: Optional[str]
    references: Optional[List['Paper']]
    cited_by: Optional[List['Paper']]
    bibtex: Optional[str]
    primary_task: Optional[str]
    secondary_task: Optional[str]
    tertiary_task: Optional[str]
    primary_method: Optional[str]
    secondary_method: Optional[str]
    tertiary_method: Optional[str]
    datasets_used: Optional[List[str]]
    metrics_used: Optional[List[str]]
    comparisons: Optional[Dict[str, PaperComparison]]
    limitations: Optional[str]

class PaperMedia(BaseModel):
    pdf_url: Optional[str]
    youtube_url: Optional[str]
    github_url: Optional[str]
    project_page_url: Optional[str]
    arxiv_url: Optional[str]

class PaperMetrics(BaseModel):
    github_star_count: Optional[int]
    github_star_avg_hype: Optional[int]
    github_star_weekly_hype: Optional[int]
    github_star_monthly_hype: Optional[int]
    github_star_tracking_start_date: Optional[str]
    github_star_tracking_latest_footprint: Optional[Dict[str, int]]
    citations_total: Optional[int]

class Paper(BaseModel):
    id: str
    arxiv_id: Optional[str] = None
    title: str
    authors: List[str]
    affiliations: Optional[List[str]] = None
    affiliations_country: Optional[List[str]] = None
    year: Optional[int] = None
    venue: Optional[str] = None
    pages: Optional[List[str]] = None
    paper_type: Optional[PaperType] = None
    session_type: Optional[PaperSessionType] = None
    accept_status: Optional[PaperAcceptStatus] = None
    note: Optional[str] = None
    content: Optional[PaperContent] = None
    media: Optional[PaperMedia] = None
    metrics: Optional[PaperMetrics] = None
    
    def __init__(self,
        id: str,
        title: str,
        authors: List[str],
        arxiv_id: Optional[str] = None,
        affiliations: Optional[List[str]] = None,
        affiliations_country: Optional[List[str]] = None,
        year: Optional[int] = None,
        venue: Optional[str] = None,
        pages: Optional[List[str]] = None,
        paper_type: Optional[PaperType] = None,
        session_type: Optional[PaperSessionType] = None,
        accept_status: Optional[PaperAcceptStatus] = None,
        note: Optional[str] = None,
        content: Optional[PaperContent] = None,
        media: Optional[PaperMedia] = None,
        metrics: Optional[PaperMetrics] = None,
    ):
        if arxiv_id is None:
            arxiv_id = detect_arxiv_id_from_citation(title)
            if arxiv_id is not None:
                media.arxiv_url = f"https://arxiv.org/abs/{arxiv_id}"

        super().__init__(
            id=id,
            title=title,
            authors=authors,
            arxiv_id=arxiv_id,
            affiliations=affiliations,
            affiliations_country=affiliations_country,
            year=year,
            venue=venue,
            pages=pages,
            paper_type=paper_type,
            session_type=session_type,
            accept_status=accept_status,
            note=note,
            content=content,
            media=media,
            metrics=metrics,
        )

PaperContent.update_forward_refs()

class PaperEdge(BaseModel):
    source: str
    target: str

class PaperGraph(BaseModel):
    nodes: List[Paper]
    edges: List[PaperEdge]