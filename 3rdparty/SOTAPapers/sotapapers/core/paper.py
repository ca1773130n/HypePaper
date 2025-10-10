import loguru
from sotapapers.core.schemas import Paper, PaperContent, PaperMedia, PaperMetrics
from sotapapers.core.models import PaperORM

def create_paper_from_schema(schema: Paper) -> PaperORM:
    orm = PaperORM(
        id=schema.id,
        arxiv_id=str(schema.arxiv_id) if schema.arxiv_id else None,
        title=schema.title,
        authors=schema.authors,
        affiliations=schema.affiliations,
        affiliations_country=schema.affiliations_country,
        year=schema.year,
        venue=schema.venue,
        pages=schema.pages,
        paper_type=schema.paper_type,
        session_type=schema.session_type,
        accept_status=schema.accept_status,
        note=schema.note,
        abstract=schema.content.abstract.replace('Abstract:', '').replace('Abstract', '').strip() if schema.content else None,
        bibtex=schema.content.bibtex if schema.content else None,
        primary_task=schema.content.primary_task if schema.content else None,
        secondary_task=schema.content.secondary_task if schema.content else None,
        tertiary_task=schema.content.tertiary_task if schema.content else None,
        primary_method=schema.content.primary_method if schema.content else None,
        secondary_method=schema.content.secondary_method if schema.content else None,
        tertiary_method=schema.content.tertiary_method if schema.content else None,
        datasets_used=schema.content.datasets_used if schema.content else None,
        metrics_used=schema.content.metrics_used if schema.content else None,
        comparisons=schema.content.comparisons if schema.content else None,
        limitations=schema.content.limitations if schema.content else None,
        pdf_url=schema.media.pdf_url if schema.media else None,
        youtube_url=schema.media.youtube_url if schema.media else None,
        github_url=schema.media.github_url if schema.media else None,
        project_page_url=schema.media.project_page_url if schema.media else None,
        arxiv_url=schema.media.arxiv_url if schema.media else None,
        github_star_count=schema.metrics.github_star_count if schema.metrics else None,
        github_star_avg_hype=schema.metrics.github_star_avg_hype if schema.metrics else None,
        github_star_weekly_hype=schema.metrics.github_star_weekly_hype if schema.metrics else None,
        github_star_monthly_hype=schema.metrics.github_star_monthly_hype if schema.metrics else None,
        github_star_tracking_start_date=schema.metrics.github_star_tracking_start_date if schema.metrics else None,
        github_star_tracking_latest_footprint=schema.metrics.github_star_tracking_latest_footprint if schema.metrics else None,
        citations_total=schema.metrics.citations_total if schema.metrics else None
    )
    return orm
    
def create_paper_from_orm(orm: PaperORM) -> Paper: 
    paper = Paper(
        id=orm.id,
        arxiv_id=orm.arxiv_id,
        title=orm.title,
        authors=orm.authors,
        affiliations=orm.affiliations,
        affiliations_country=orm.affiliations_country,
        year=orm.year,
        venue=orm.venue,
        pages=orm.pages,
        paper_type=orm.paper_type,
        session_type=orm.session_type,
        accept_status=orm.accept_status,
        note=orm.note,
        content=PaperContent(
            abstract=orm.abstract,
            bibtex=orm.bibtex,
            references=None,
            cited_by=None,
            primary_task=orm.primary_task,
            secondary_task=orm.secondary_task,
            tertiary_task=orm.tertiary_task,
            primary_method=orm.primary_method,
            secondary_method=orm.secondary_method,
            tertiary_method=orm.tertiary_method,
            datasets_used=orm.datasets_used,
            metrics_used=orm.metrics_used,
            comparisons=orm.comparisons,
            limitations=orm.limitations
        ),
        media=PaperMedia(
            pdf_url=orm.pdf_url,
            youtube_url=orm.youtube_url,
            github_url=orm.github_url,
            project_page_url=orm.project_page_url,
            arxiv_url=orm.arxiv_url,
        ),
        metrics=PaperMetrics(
            github_star_count=orm.github_star_count,
            github_star_avg_hype=orm.github_star_avg_hype,
            github_star_weekly_hype=orm.github_star_weekly_hype,
            github_star_monthly_hype=orm.github_star_monthly_hype,
            github_star_tracking_start_date=orm.github_star_tracking_start_date,
            github_star_tracking_latest_footprint=orm.github_star_tracking_latest_footprint,
            citations_total=orm.citations_total,
        )
    )
    return paper
     
class PaperDataDump:
    def __init__(self, logger: loguru.logger):
        self.logger = logger
    
    def dump(self, paper: Paper):
        self.logger.info(f"Title: {paper.title}")
        self.logger.info(f"Authors: {paper.authors}")
        self.logger.info(f"Year: {paper.year}")
        self.logger.info(f"Venue: {paper.venue}")
        self.logger.info(f"Abstract: {paper.content.abstract}")
        self.logger.info(f"Pages: {paper.pages}")
        self.logger.info(f"Paper type: {paper.paper_type}")
        self.logger.info(f"Session type: {paper.session_type}")
        self.logger.info(f"Note: {paper.note}")

    def score(self, paper: Paper):
        num_citations = paper.metrics.citations_total
        speed = paper.metrics.github_star_avg_hype
        return num_citations + speed