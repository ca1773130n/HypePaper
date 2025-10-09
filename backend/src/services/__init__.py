"""Services package for business logic.

Exports all service classes.
"""
from .hype_score_service import HypeScoreService
from .metric_service import MetricService
from .paper_service import PaperService
from .topic_matching_service import TopicMatchingService
from .topic_service import TopicService

# SOTAPapers legacy integration services
from .arxiv_service import AsyncArxivService
from .github_service import AsyncGitHubService, GitHubRepo
from .pdf_service import PDFAnalysisService
from .llm_service import AsyncLLMService, OpenAILLMService, LlamaCppLLMService
from .citation_service import CitationMatcher
from .config_service import ConfigService, get_config_service
from .pdf_storage_service import PDFStorageService, get_storage_service

__all__ = [
    # Original services
    "PaperService",
    "TopicService",
    "MetricService",
    "HypeScoreService",
    "TopicMatchingService",
    # SOTAPapers integration services
    "AsyncArxivService",
    "AsyncGitHubService",
    "GitHubRepo",
    "PDFAnalysisService",
    "AsyncLLMService",
    "OpenAILLMService",
    "LlamaCppLLMService",
    "CitationMatcher",
    "ConfigService",
    "get_config_service",
    "PDFStorageService",
    "get_storage_service",
]
