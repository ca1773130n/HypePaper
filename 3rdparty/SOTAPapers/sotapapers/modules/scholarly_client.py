from typing import List
import loguru
import time
import random
import os
import signal
import functools
import errno
from pathlib import Path
import sys
import logging

from sotapapers.core.settings import Settings
from sotapapers.core.schemas import Paper, PaperContent, PaperMedia, PaperMetrics, PaperType, PaperSessionType, PaperAcceptStatus
from sotapapers.utils.id_util import make_generated_id
from sotapapers.utils.string_util import compare_strings_with_tolerance

from scholarly import scholarly, ProxyGenerator

# Set up a proxy generator (e.g., using FreeProxies)
pg = ProxyGenerator()
pg.FreeProxies() # Or pg.ScraperAPI(api_key="YOUR_SCRAPERAPI_KEY") etc.
scholarly.proxy_generator = pg

class TimeoutException(Exception):
    pass

def timeout(seconds=10, error_message=os.strerror(errno.ETIME)):
    def decorator(func):
        def _handle_timeout(signum, frame):
            raise TimeoutException(error_message)

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            signal.signal(signal.SIGALRM, _handle_timeout)
            signal.alarm(seconds)
            try:
                result = func(*args, **kwargs)
            finally:
                signal.alarm(0) # Disable the alarm
            return result
        return wrapper
    return decorator

class ScholarlyClient:
    def __init__(self, settings: Settings, logger: loguru.logger):
        self.settings = settings
        self.log = logger
        self.max_results_by_keyword = int(self.settings.config.paper_search_client.scholarly.max_results_by_keyword)
        self.max_results = int(self.settings.config.paper_search_client.scholarly.max_results)
        self.max_retry = int(self.settings.config.paper_search_client.scholarly.max_retry)
        self.retry_delay_sec = int(self.settings.config.paper_search_client.scholarly.retry_delay_sec)

    def search(self, keyword: str) -> List[Paper]:
        return self.search_by_title(keyword)

    @timeout(seconds=30) # Apply timeout to search_pubs
    def _search_pubs_with_timeout(self, title: str):
        return scholarly.search_pubs(title)

    @timeout(seconds=30) # Apply timeout to citedby
    def _citedby_with_timeout(self, result):
        return scholarly.citedby(result)

    def search_by_title(self, title: str) -> Paper:
        delay_sec = self.retry_delay_sec
        for i in range(self.max_retry):
            try:
                query = self._search_pubs_with_timeout(title)
                for result in query:
                    if not compare_strings_with_tolerance(result['bib']['title'], title, 2):
                        continue

                    paper = self._make_paper_object(result)

                    # get citing papers first
                    citing_papers = []
                    if result['num_citations'] > 0:
                        citings = self._citedby_with_timeout(result)
                        for c in citings:
                            citing_paper = self._make_paper_object(c)
                            citing_paper.content.references = [paper]
                            citing_papers.append(citing_paper)

                    paper.content.cited_by = citing_papers
                    return paper
            except TimeoutException as e:
                self.log.error(f'Scholarly search timed out for title: {title}: {e} / retrying ({i+1}/{self.max_retry})')
                time.sleep(delay_sec)
                delay_sec *= random.uniform(1.0, 2.0)
            except Exception as e:
                self.log.error(f'Failed to search scholarly for title: {title}: {e} / retrying ({i+1}/{self.max_retry})')
                time.sleep(delay_sec)
                delay_sec *= random.uniform(1.0, 2.0) 
        return None

    def _make_paper_object(self, result) -> Paper:
        abstract = result['bib']['abstract']
        if abstract is not None:
            abstract = abstract.replace('\n', ' ')

        authors = result['bib']['author']
        title = result['bib']['title']
        venue = result['bib']['venue']
        year = result['bib']['pub_year']
        citations = result['num_citations']

        pdf_url = result['eprint_url']

        paper = Paper(
            id=make_generated_id(title, year),
            title=title,
            authors=authors,
            year=year,
            venue=venue,
            content=PaperContent(
                abstract=abstract,
                references=None,
                cited_by=None,
                bibtex=None,
                primary_task=None,
                secondary_task=None,
                tertiary_task=None,
                primary_method=None,
                secondary_method=None,
                tertiary_method=None,
                datasets_used=None,
                metrics_used=None,
                comparisons=None,
                limitations=None
            ),
            media=PaperMedia(
                pdf_url=pdf_url,
                arxiv_url=None,
                youtube_url=None,
                github_url=None,
                project_page_url=None
            ),
            metrics=PaperMetrics(
                citations_total=citations,
                github_star_count=None,
                github_star_avg_hype=None,
                github_star_weekly_hype=None,
                github_star_monthly_hype=None,
                github_star_tracking_start_date=None,
                github_star_tracking_latest_footprint=None
            ),
            paper_type=PaperType.UNKNOWN,
            session_type=PaperSessionType.UNKNOWN,
            accept_status=PaperAcceptStatus.UNKNOWN,
            note=None
        )
        return paper

if __name__ == "__main__":
    # This is a test function for ScholarlyClient
    logging.basicConfig(level=logging.DEBUG) # Configure standard logging for scholarly's internal messages

    from sotapapers.core.schemas import Paper, PaperContent, PaperMedia, PaperMetrics # Import Paper schema

    settings = Settings(Path('sotapapers/configs'))
    logger = loguru.logger
    # logger.remove() # Removed as we want to see scholarly's internal log
    # logger.add(sys.stderr, level="DEBUG") # Removed as we want to see scholarly's internal log

    client = ScholarlyClient(settings, logger)

    # Create a dummy paper for testing
    dummy_paper = Paper(
        id="test_id",
        arxiv_id="1706.03762",
        title="Attention Is All You Need",
        authors=["Ashish Vaswani", "Noam Shazeer", "Niki Parmar", "Jakob Uszkoreit", "Llion Jones", "Aidan N. Gomez", "Łukasz Kaiser", "Illia Polosukhin"],
        year=2017,
        venue="NeurIPS",
        pages=[],
        paper_type=PaperType.CONFERENCE_PAPER,
        session_type=PaperSessionType.ORAL,
        accept_status=PaperAcceptStatus.NORMAL,
        note="",
        affiliations=[],
        affiliations_country=[],
        content=PaperContent(
            abstract="",
            references=[],
            cited_by=[],
            bibtex="",
            primary_task="",
            secondary_task="",
            tertiary_task="",
            primary_method="",
            secondary_method="",
            tertiary_method="",
            datasets_used=[],
            metrics_used=[],
            comparisons={},
            limitations="",
        ), # Initialize with default empty content
        media=PaperMedia(
            pdf_url="",
            youtube_url="",
            github_url="",
            project_page_url="",
            arxiv_url="",
        ), # Initialize with default empty media
        metrics=PaperMetrics(
            github_star_count=0,
            github_star_avg_hype=0,
            github_star_weekly_hype=0,
            github_star_monthly_hype=0,
            github_star_tracking_start_date="",
            github_star_tracking_latest_footprint={},
            citations_total=0,
        ) # Initialize with default empty metrics
    )

    logger.info(f"Searching for paper: {dummy_paper.title}")
    found_paper = client.search_by_title(dummy_paper.title)

    if found_paper:
        logger.info(f"Found paper: {found_paper.title}")
        if found_paper.content.cited_by:
            logger.info(f"Found {len(found_paper.content.cited_by)} citing papers:")
            for cited_paper in found_paper.content.cited_by:
                logger.info(f"- {cited_paper.title} by {', '.join(cited_paper.authors)}")
        else:
            logger.info("No citing papers found for the dummy paper.")
    else:
        logger.info("Paper not found by ScholarlyClient.")