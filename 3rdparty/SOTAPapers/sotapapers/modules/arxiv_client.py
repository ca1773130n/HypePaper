import requests
import arxiv
import time
import random
import loguru
import requests

from sotapapers.core.settings import Settings
from sotapapers.core.schemas import Paper, PaperType, PaperMedia, PaperMetrics, PaperContent, PaperSessionType, PaperAcceptStatus
from sotapapers.modules.paper_search_client import PaperSearchClient
from typing import List, Optional

from sotapapers.utils.id_util import make_generated_id
from sotapapers.utils.string_util import compare_strings_with_tolerance

class ArxivClient(PaperSearchClient):
    def __init__(self, settings: Settings, logger: loguru.logger):
        self.settings = settings
        self.log = logger

        self.max_results_by_keyword = int(self.settings.config.paper_search_client.arxiv.max_results_by_keyword)
        self.max_results = int(self.settings.config.paper_search_client.arxiv.max_results)
        self.max_retry = int(self.settings.config.paper_search_client.arxiv.max_retry)
        self.retry_delay_sec = int(self.settings.config.paper_search_client.arxiv.retry_delay_sec)

    def search(self, keyword: str) -> List[Paper]:
        self.log.info(f'Searching for papers with keyword: {keyword} (max limit: {self.max_results_by_keyword})')

        search_engine = arxiv.Search(
            query=keyword,
            max_results=self.max_results_by_keyword,
            sort_by=arxiv.SortCriterion.SubmittedDate
        )

        results = list(search_engine.results())
        papers = []
        
        self.log.info(f'Got [{len(list(results))}] papers for keyword: {keyword}')

        for result in results:
            self.log.debug(f'Found arXiv paper for [{result.get_short_id()}]: {result.title}')
            paper_object = self._make_paper_object(result)
            papers.append(paper_object)
        return papers

    def search_by_title(self, title: str) -> Optional[Paper]:
        self.log.info(f'Searching for paper with title on arXiv: {title}')
        delay_sec = self.retry_delay_sec
       
        results = [] 
        for i in range(self.max_retry):
            try:
                search_engine = arxiv.Search(
                    query=f'ti: "{title}"',
                    max_results=self.max_results,
                    sort_by=arxiv.SortCriterion.Relevance
                )
                results.extend(list(search_engine.results()))
                if len(results) > 0:
                    break
            except Exception as e:
                self.log.error(f'Error searching for paper with title: {title}: {e} / retrying ({i+1}/{self.max_retry})')
                time.sleep(delay_sec)
                delay_sec *= random.uniform(1.0, 2.0)
            
        if len(results) == 0:
            return None
        
        for r in results:
            if compare_strings_with_tolerance(r.title, title):
                self.log.debug(f'Found arXiv paper [{r.get_short_id()}] with title: {title}')
                return self._make_paper_object(r)
        return None
    
    def search_by_id(self, id: str) -> Paper:
        self.log.info(f'Searching for paper with id on arXiv: {id}')
        delay_sec = self.retry_delay_sec
        
        for i in range(self.max_retry):
            try:
                search_engine = arxiv.Search(
                    id_list=[id],
                    max_results=self.max_results,
                    sort_by=arxiv.SortCriterion.Relevance
                )
                results = list(search_engine.results())
                if len(results) > 0:
                    break
            except Exception as e:
                self.log.error(f'Error searching for paper with id: {id}: {e} / retrying ({i+1}/{self.max_retry})')
                time.sleep(delay_sec)
                delay_sec *= random.uniform(1.0, 2.0)
        
        if len(results) == 0:
            return None
        
        for r in results:
            if r.get_short_id() == id:
                return self._make_paper_object(r)
        return None
   
    def get_arxiv_url_from_title(self, title: str) -> str:
        self.log.info(f'Searching for arxiv url with title: {title}')
        search_engine = arxiv.Search(
            query=title,
            max_results=10,
            sort_by=arxiv.SortCriterion.Relevance
        )
        results = list(search_engine.results())
        if len(results) == 0:
            return None
        if not compare_strings_with_tolerance(results[0].title, title):
            return None
        return f'https://arxiv.org/abs/{results[0].entry_id}'
    
    def _make_paper_object(self, result) -> Paper:
        arxiv_url = result.entry_id
        paper_short_id = result.get_short_id()
        paper_title = result.title
        paper_authors = [author.name for author in result.authors]
        paper_year = result.published.date().year

        try:
            response = requests.get(f"https://arxiv.org/bibtex/{paper_short_id}")
            paper_bibtex = response.text
        except Exception as e:
            self.log.error(f'Error getting bibtex for paper: {paper_short_id}: {e}')
            paper_bibtex = None

        paper_update_time = result.updated.date()
        paper_citation_count = 0
        paper_url = result.entry_id

        paper_venue = result.primary_category
        paper_references = []
        paper_abstract = result.summary

        pdf_url = result.pdf_url
        youtube_url = None
        github_url = None
        project_page_url = None
 
        paper_media = PaperMedia(
            pdf_url=pdf_url,
            youtube_url=youtube_url,
            github_url=github_url,
            project_page_url=project_page_url,
            arxiv_url=arxiv_url
        )
       
        github_star_count = 0
        github_star_avg_hype = 0
        github_star_weekly_hype = 0
        github_star_monthly_hype = 0
        github_star_tracking_start_date = None
        github_star_tracking_latest_footprint = None
        citations_total = None
        
        paper_metrics = PaperMetrics(
            github_star_count=github_star_count,
            github_star_avg_hype=github_star_avg_hype,
            github_star_weekly_hype=github_star_weekly_hype,
            github_star_monthly_hype=github_star_monthly_hype,
            github_star_tracking_start_date=github_star_tracking_start_date,
            github_star_tracking_latest_footprint=github_star_tracking_latest_footprint,
            citations_total=citations_total
        )
        
        paper_type = PaperType.ARXIV_PAPER
        paper_venue = None
        paper_pages = None
        paper_session_type = PaperSessionType.UNKNOWN
        paper_accept_status = PaperAcceptStatus.UNKNOWN
        paper_note = None

        paper_content = PaperContent(
            abstract=paper_abstract,
            references=paper_references,
            cited_by=None,
            bibtex=paper_bibtex,
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
        )
 
        paper_object = Paper(
            id=make_generated_id(paper_title, paper_year),
            arxiv_id=paper_short_id,
            title=paper_title,
            authors=paper_authors,
            year=paper_year,
            venue=paper_venue,
            pages=paper_pages,
            paper_type=paper_type,
            session_type=paper_session_type,
            accept_status=paper_accept_status,
            note=paper_note,
            content=paper_content,
            media=paper_media,
            metrics=paper_metrics
        )
        return paper_object