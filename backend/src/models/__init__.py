"""SQLAlchemy models for HypePaper."""

from .base import Base
from .paper import Paper

# Legacy models (if they exist)
try:
    from .hype_score import HypeScore
    from .metric_snapshot import MetricSnapshot
    from .paper_topic_match import PaperTopicMatch
    from .topic import Topic

    __all__ = [
        "Base",
        "Paper",
        "Topic",
        "PaperTopicMatch",
        "MetricSnapshot",
        "HypeScore",
    ]
except ImportError:
    __all__ = [
        "Base",
        "Paper",
    ]
