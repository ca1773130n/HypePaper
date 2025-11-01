"""SQLAlchemy models for HypePaper."""

from .base import Base
from .paper import Paper

# Legacy models
from .topic import Topic
from .paper_topic_match import PaperTopicMatch
from .metric_snapshot import MetricSnapshot

# SOTAPapers integration models
from .author import Author, PaperAuthor
from .paper_reference import PaperReference
from .github_metrics import GitHubMetrics, GitHubStarSnapshot
from .pdf_content import PDFContent
from .llm_extraction import LLMExtraction, ExtractionType, VerificationStatus
from .admin_task_log import AdminTaskLog
from .crawler_job import CrawlerJob
from .citation_snapshot import CitationSnapshot
from .vote import Vote
from .user_profile import UserProfile

__all__ = [
    "Base",
    "Paper",
    "Topic",
    "PaperTopicMatch",
    "MetricSnapshot",
    "Author",
    "PaperAuthor",
    "PaperReference",
    "GitHubMetrics",
    "GitHubStarSnapshot",
    "PDFContent",
    "LLMExtraction",
    "ExtractionType",
    "VerificationStatus",
    "AdminTaskLog",
    "CrawlerJob",
    "CitationSnapshot",
    "Vote",
    "UserProfile",
]
