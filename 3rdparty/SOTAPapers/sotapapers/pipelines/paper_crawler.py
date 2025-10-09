import multiprocessing as mp
import argparse
import multiprocessing
import os
import loguru
import requests
import sys
from selenium import webdriver

from sotapapers.core.schemas import Paper, PaperContent, PaperMedia, PaperMetrics, PaperType, PaperSessionType, PaperAcceptStatus, PaperComparison
from sotapapers.core.paper import PaperDataDump
from sotapapers.core.database import DataBase
from sotapapers.core.settings import Settings, CrawlMode
from sotapapers.modules.paper_reader import PaperReader
from sotapapers.modules.arxiv_client import ArxivClient
from sotapapers.modules.semantic_scholar_client import SemanticScholarClient
from sotapapers.modules.github_repo_searcher import GitHubRepoSearcher
from sotapapers.modules.google_scholar_scraper import GoogleScholarScraper
from sotapapers.modules.web_scraper import WebScraper
from sotapapers.utils.config import get_config_path
from sotapapers.utils.id_util import make_generated_id
from sotapapers.utils.url_utils import apply_url_prefix

from pathlib import Path
from time import sleep

class PaperCrawler:
    def __init__(self, settings: Settings, logger: loguru.logger, request_timeout: int = 300):
        self.settings = settings
        self.log = logger
        self.web_scraper = WebScraper(settings, logger, request_timeout=request_timeout)
        self.paper_reader = PaperReader(settings, logger)

        self.arxiv = ArxivClient(settings, logger)
        self.semantic_scholar = SemanticScholarClient(settings, logger)
        self.github_repo_searcher = GitHubRepoSearcher(self.settings, self.log, request_timeout=request_timeout)
        self.paper_data_dump = PaperDataDump(self.log)

    def run(self, keywords: list[str] = []):
        db = DataBase(self.settings.config.database.url, self.log)
        try:
            if self.settings.mode == CrawlMode.CONFERENCE_PAPERS:
                papers = self.grab_conference_papers(db, mandatory_keywords=keywords, crawl_references=True)
            elif self.settings.mode == CrawlMode.KEYWORD_SEARCH:
                keyword_query_string = ' '.join(keywords)
                papers = self.grab_keyword_search_papers(db, keyword_query_string)
            else:
                raise ValueError(f'Invalid mode: {self.settings.mode}')
        finally:
            db.dispose()

    @staticmethod
    def _update_paper_metrics(paper: Paper, arxiv_client: ArxivClient, semantic_scholar_client: SemanticScholarClient, github_repo_searcher: GitHubRepoSearcher, logger: loguru.logger):
        if paper.paper_type != PaperType.ARXIV_PAPER and paper.arxiv_id is None:
            # get arxiv paper and its short id
            arxiv_paper = arxiv_client.search_by_title(paper.title)
            if arxiv_paper is not None:
                paper.arxiv_id = arxiv_paper.arxiv_id
                paper.media.arxiv_url = arxiv_paper.media.arxiv_url
            else:
                logger.warning(f'No arxiv paper found for: {paper.title}')
                return

        # get citation number from semantic scholar
        num_citations = 0
        if paper.metrics.citations_total is None or paper.metrics.citations_total <= 0:
            semantic_scholar_paper = semantic_scholar_client.search_by_title(paper.title)
            if semantic_scholar_paper is not None:
                num_citations = semantic_scholar_paper.metrics.citations_total
                paper.metrics.citations_total = num_citations

        # get GitHub star count and tracking info
        github_repo_search_result = github_repo_searcher.search_github_project(paper.title, paper.arxiv_id)
        if github_repo_search_result is not None:
            if github_repo_search_result.code_link is not None:
                paper.media.github_url = github_repo_search_result.code_link
            
            stars = github_repo_search_result.stars
            age = github_repo_search_result.age
            paper.metrics.github_star_count = stars
            paper.metrics.github_star_tracking_start_date = github_repo_search_result.creation_date
            paper.metrics.github_star_tracking_latest_footprint = github_repo_search_result.age
            logger.debug(f'Got GitHub repo for paper: {paper.title} (num stars: {paper.metrics.github_star_count}, creation date: {paper.metrics.github_star_tracking_start_date})')
        else:
            stars = -1
            age = -1
        
        if num_citations > 0:
            num_stars = 0 if stars == -1 else stars
            speed = (num_citations * 100 + num_stars) / age if age > 0 else 0
        else:
            speed = stars / age if stars > 0 and age > 0 else 0

        paper.metrics.github_star_avg_hype = speed
        
    def grab_keyword_search_papers(self, db: DataBase, keyword: str):
        # search paper on arxiv first
        papers = self.arxiv.search(keyword)

        # get github repo for each paper
        for paper in papers:
            PaperCrawler._update_paper_metrics(paper, self.arxiv, self.semantic_scholar, self.github_repo_searcher, self.log)
            self.paper_data_dump.dump(paper)
        return papers
    
    def grab_conference_papers(self, db: DataBase, mandatory_keywords: list[str] = [], additional_keywords: list[str] = [], crawl_references: bool = False):
        all_papers = []
        for conference in self.settings.config.conference_papers:
            conference_name = conference['conference_name']
            
            for a_conference in conference['conferences']:
                url = a_conference['url']
                year = a_conference['year']
                self.log.debug(f'scraping {conference_name} {year} paper list from: {url}')

                papers = self._grab_conference_papers_papercopilot(conference_name, url, year, mandatory_keywords, additional_keywords, crawl_references)
                all_papers.extend(papers)
        return all_papers
   
    @staticmethod
    def _get_conference_papers_list(html: str, table_id: str, conference_name: str, mandatory_keywords: list[str] = [], additional_keywords: list[str] = [], settings: Settings = None, logger: loguru.logger = None) -> list[tuple]:
        if settings is None:
            # Fallback if settings are not explicitly passed (e.g., if called directly)
            from sotapapers.core.settings import Settings
            settings = Settings(Path("sotapapers/configs"))
        if logger is None:
            import loguru
            logger = loguru.logger

        temp_web_scraper = WebScraper(settings, logger, request_timeout=settings.config.paper_crawler.request_timeout) # Initialize WebScraper locally
        table = temp_web_scraper.get_table_from_html(html, table_id)
        header_tr = table.find('thead').find_all('tr')[1]
        header_th = header_tr.find_all('th')
        headers = [header.get_text(strip=True) for header in header_th]

        logger.debug(f'got table headers: {headers}')

        rows = table.find('tbody').find_all('tr')
        
        pdf_link_text = 'PDF'
        youtube_link_text = 'Youtube'
        github_link_text = 'Github'
        project_page_link_text = 'Project Page'
        arxiv_link_text = 'Arxiv'
        
        if conference_name == 'CVPR':
            conf_url_text = 'CVF'
        elif conference_name == 'ICLR':
            conf_url_text = 'OR'
        else:
            raise ValueError(f'Invalid conference name: {conference_name}')
        
        rows_in_raw_data = []
        
        for row in rows:
            tds = row.find_all('td')

            title_col = tds[2]
            authors_col = tds[4]
            affiliations_col = tds[5]
            affiliations_country_col = tds[6]
            status_col = tds[7]
            citations_col = tds[8]

            title_a = title_col.find('a')
            title = title_a.text
            url = title_a['href']
            
            authors_list = authors_col.get('data-val').split(';')
            affiliations_list = affiliations_col.get('data-val').split(';')
            affiliations_country_list = affiliations_country_col.get('data-val').split(';')
            session_type = status_col.get('data-val')
            citations_str = citations_col.get('data-val')
            citations = int(citations_str) if citations_str is not None and citations_str.isdigit() else 0

            pdf_url = None
            youtube_url = None
            github_url = None
            project_page_url = None
            arxiv_url = None
            conf_url = None

            social_links_span = title_col.find('span')
            social_links_ul = social_links_span.find('ul')

            if social_links_ul is not None:
                social_links_lis = social_links_ul.find_all('li')

                for social_links_li in social_links_lis:
                    social_link_a = social_links_li.find('a')
                    social_link_a_href = social_link_a['href']
                    social_link_a_title = social_link_a['title']

                    if social_link_a_title == pdf_link_text:
                        pdf_url = social_link_a_href
                    elif social_link_a_title == youtube_link_text:
                        youtube_url = social_link_a_href
                    elif social_link_a_title == github_link_text:
                        github_url = social_link_a_href
                    elif social_link_a_title == project_page_link_text:
                        project_page_url = social_link_a_href
                    elif social_link_a_title == arxiv_link_text:
                        arxiv_url = social_link_a_href
                    elif social_link_a_title == conf_url_text:
                        conf_url = social_link_a_href

            if conf_url is None:
                conf_url = url

            rows_in_raw_data.append([title, url, conf_url, None, authors_list, affiliations_list, affiliations_country_list, session_type, citations, pdf_url, youtube_url, github_url, project_page_url, arxiv_url])

        return rows_in_raw_data

    def _grab_conference_papers_papercopilot(self, conference_name: str, url: str, year: int, mandatory_keywords: list[str] = [], additional_keywords: list[str] = [], crawl_references: bool = False):
        # Initialize WebScraper locally for this method
        temp_web_scraper = WebScraper(self.settings, self.log)
        temp_web_scraper.fetch_url(url)

        button_name = 'btn_fetchall'
        temp_web_scraper.click_element_by_id(button_name, wait_timeout=30, max_attempts=2, sleep_sec=5)

        sleep_sec = 10
        self.log.debug(f'waiting for {sleep_sec} seconds to load paper list')
        sleep(sleep_sec)

        papers = []
        page_source = temp_web_scraper.current_page_source()
        settings_dict = self.settings.to_dict()
        use_multiprocessing = True

        # Get raw data and prepare arguments for multiprocessing
        raw_paper_data = PaperCrawler._get_conference_papers_list(page_source, 'paperlist', conference_name, mandatory_keywords, additional_keywords, self.settings, self.log)
        num_papers = len(raw_paper_data)
        
        self.log.info(f'found {num_papers} papers')

        num_processes = min(multiprocessing.cpu_count(), num_papers)

        # get abstract by multiprocessing
        row_args_abstract = []
        for row_in_raw_data in raw_paper_data:
            status = row_in_raw_data[7]
            if 'rejected' in status.lower():
                continue
            row_args_abstract.append((row_in_raw_data[2], settings_dict))

        self.log.debug(f'getting abstracts from papers by: {num_processes} processes')
        
        with multiprocessing.Pool(processes=num_processes) as pool:
            abstract_list = pool.starmap(PaperCrawler._get_abstract_from_conference_website, row_args_abstract)

        # Prepare arguments for starmap
        row_args = []
        i = 0
        for row_in_raw_data in raw_paper_data:
            title = row_in_raw_data[0]
            status = row_in_raw_data[7]

            if 'rejected' in status.lower():
                continue
            
            matched_keywords = [keyword for keyword in mandatory_keywords if keyword.lower() in title.lower().split(' ')]

            abstract = abstract_list[i]
            matched_additional_keywords = [keyword for keyword in additional_keywords if keyword.lower() in abstract.lower().split(' ')]
            i += 1

            if len(matched_keywords) < len(mandatory_keywords) / 2.0 or len(matched_additional_keywords) < len(additional_keywords) / 4.0:
                self.log.debug(f'skipping paper: {title} (matched_keywords: {matched_keywords}, matched_additional_keywords: {matched_additional_keywords})')
                self.log.debug(f'mandatory_keywords: {mandatory_keywords}, additional_keywords: {additional_keywords}')
                continue 

            row_in_raw_data[3] = abstract
            row_args.append((tuple(row_in_raw_data), settings_dict, conference_name, year, mandatory_keywords, additional_keywords))

        with multiprocessing.Pool(processes=num_processes) as pool:
            results = pool.starmap(PaperCrawler._scrape_paper_info_papercopilot_single, row_args)
            for p in results:
                if p is not None:
                    papers.append(p)

        return papers

    def _grab_reference_papers(logger: loguru.logger, db: DataBase, paper: Paper, year_after: int, mandatory_keywords: list[str], additional_keywords: list[str], recursive_depth: int = 1):
        if paper.content.references is None:
            return
        
        if recursive_depth <= 0:
            return
        
        for ref_paper in paper.content.references:
            if int(ref_paper.year) < year_after or recursive_depth == 0:
                continue

            matched_keywords = [keyword for keyword in mandatory_keywords if keyword.lower() in ref_paper.title.lower().split(' ')]
            matched_additional_keywords = [keyword for keyword in additional_keywords if keyword.lower() in ref_paper.content.abstract.lower().split(' ')]

            if len(matched_keywords) < len(mandatory_keywords) / 2.0 or len(matched_additional_keywords) < len(additional_keywords) / 4.0:
                continue
            
            logger.debug(f'grabbing reference paper: {ref_paper.title} (year: {ref_paper.year}, recursive_depth: {recursive_depth})')
            looked_paper = PaperCrawler._lookup_paper(logger, ref_paper)
            
            # Re-initialize clients locally for multiprocessing safety if called from a worker
            temp_settings = Settings(Path("sotapapers/configs")) # Re-initialize settings in the worker
            temp_arxiv = ArxivClient(temp_settings, logger)
            temp_scholarly_client = SemanticScholarClient(temp_settings, logger)
            temp_github_repo_searcher = GitHubRepoSearcher(temp_settings, logger)
            
            PaperCrawler._update_paper_metrics(looked_paper, temp_arxiv, temp_scholarly_client, temp_github_repo_searcher, logger)
            db.insert_paper(looked_paper)
            db.dispose()
            
            if looked_paper is not None:
                PaperCrawler._grab_reference_papers(logger, db, looked_paper, year_after, recursive_depth - 1)

    def _grab_citing_papers(logger: loguru.logger, db: DataBase, paper: Paper, year_after: int, mandatory_keywords: list[str], additional_keywords: list[str], recursive_depth: int = 1):
        temp_settings = Settings(Path("sotapapers/configs"))
        temp_google_scholar_scraper = GoogleScholarScraper(temp_settings, logger)
        temp_google_scholar_scraper.search_citing_papers(paper)

        db.insert_paper(paper)
        db.dispose()
        
        if recursive_depth <= 0:
            return
       
        if paper.content.cited_by is None:
            return
        
        logger.debug(f'grabbing citing papers for {paper.title} (year: {paper.year}, recursive_depth: {recursive_depth})')
        
        for citing_paper in paper.content.cited_by:
            if int(citing_paper.year) < year_after or recursive_depth == 0:
                continue
            
            matched_keywords = [keyword for keyword in mandatory_keywords if keyword.lower() in citing_paper.title.lower().split(' ')]
            matched_additional_keywords = [keyword for keyword in additional_keywords if keyword.lower() in citing_paper.content.abstract.lower().split(' ')]

            if len(matched_keywords) < len(mandatory_keywords) / 2.0 or len(matched_additional_keywords) < len(additional_keywords) / 4.0:
                continue
            
            temp_arxiv = ArxivClient(temp_settings, logger)
            temp_scholarly_client = SemanticScholarClient(temp_settings, logger)
            temp_github_repo_searcher = GitHubRepoSearcher(temp_settings, logger)
            PaperCrawler._update_paper_metrics(citing_paper, temp_arxiv, temp_scholarly_client, temp_github_repo_searcher, logger)

            db.insert_paper(citing_paper)
            db.dispose()
            PaperCrawler._grab_citing_papers(logger, db, citing_paper, year_after, recursive_depth - 1) 

    def _grab_citing_papers_semantic_scholar(logger: loguru.logger, db: DataBase, paper: Paper, year_after: int, mandatory_keywords: list[str], additional_keywords: list[str], recursive_depth: int = 1):
        temp_settings = Settings(Path("sotapapers/configs")) # Re-initialize settings in the worker

        temp_scholarly_client = SemanticScholarClient(temp_settings, logger)
        searched_paper = temp_scholarly_client.search_by_title(paper.title)

        if searched_paper is not None and searched_paper.content is not None:
            paper.content.cited_by = searched_paper.content.cited_by

        db.insert_paper(paper)
        db.dispose()

        if recursive_depth <= 0:
            return
       
        if paper.content.cited_by is None:
            return
        
        logger.debug(f'grabbing citing papers for {paper.title} (year: {paper.year}, recursive_depth: {recursive_depth})')
        
        for citing_paper in paper.content.cited_by:
            if int(citing_paper.year) < year_after or recursive_depth == 0:
                continue
            
            matched_keywords = [keyword for keyword in mandatory_keywords if keyword.lower() in citing_paper.title.lower().split(' ')]
            matched_additional_keywords = [keyword for keyword in additional_keywords if keyword.lower() in citing_paper.content.abstract.lower().split(' ')]

            if len(matched_keywords) < len(mandatory_keywords) / 2.0 or len(matched_additional_keywords) < len(additional_keywords) / 4.0:
                continue
            
            temp_arxiv = ArxivClient(temp_settings, logger)
            temp_github_repo_searcher = GitHubRepoSearcher(temp_settings, logger)
            PaperCrawler._update_paper_metrics(citing_paper, temp_arxiv, temp_scholarly_client, temp_github_repo_searcher, logger)

            db.insert_paper(citing_paper)
            db.dispose()
            PaperCrawler._grab_citing_papers(logger, db, citing_paper, year_after, recursive_depth - 1)

    def _lookup_paper(logger: loguru.logger, ref_paper):
        logger.debug(f'looking up reference paper: {ref_paper.title} (type: {ref_paper.paper_type})')
        #if ref_paper.paper_type == PaperType.ARXIV_PAPER:
        return PaperCrawler._lookup_paper_arxiv(logger, ref_paper)
    
    def _lookup_paper_arxiv(logger: loguru.logger, ref_paper):
        # Initialize WebScraper and PaperReader locally for multiprocessing safety if called from a worker
        temp_settings = Settings(Path("sotapapers/configs")) # Re-initialize settings with Path
        temp_web_scraper = WebScraper(temp_settings, logger, request_timeout=temp_settings.config.paper_crawler.request_timeout)
        temp_paper_reader = PaperReader(temp_settings, logger)
        temp_arxiv = ArxivClient(temp_settings, logger)

        searched_arxiv_paper = temp_arxiv.search_by_title(ref_paper.title)
        if searched_arxiv_paper is None:
            return None
        
        ref_paper.media.pdf_url = searched_arxiv_paper.media.pdf_url
        ref_paper.media.arxiv_url = searched_arxiv_paper.media.arxiv_url
        ref_paper.year = searched_arxiv_paper.year

        pdf_download_basepath = temp_settings.config.paper_crawler.pdf_download_basepath
        pdf_save_dir = Path(f'{pdf_download_basepath}/arxiv/{ref_paper.year}')
        pdf_save_dir.mkdir(parents=True, exist_ok=True)
        pdf_save_path = pdf_save_dir / f'{ref_paper.title}.pdf'
        
        PaperCrawler._download_pdf(ref_paper.media.pdf_url, temp_settings, pdf_save_path)
        temp_paper_reader.set_file_path(pdf_save_path)

        #ref_paper.content.references = temp_paper_reader.extract_references_arxiv(ref_paper)
        return ref_paper

    def _lookup_paper_doi(self, paper: Paper):
        temp_settings = Settings(Path("sotapapers/configs")) # Re-initialize settings with Path
        url = apply_url_prefix("https://api.crossref.org/works", temp_settings)
        params = {
            "query.title": paper.title,
            "rows": 1
        }
        
        response = requests.get(url, params=params)
        data = response.json()
        
        if data['message']['items']:
            paper = data['message']['items'][0]
            doi = paper.get('DOI', None)
            if doi:
                return apply_url_prefix(f"https://doi.org/{doi}", temp_settings)
            else:
                self.log.warning(f'No DOI found for paper: {paper.title}')
                return None
        else:
            self.log.warning(f'No paper found for DOI: {paper.title}')
            return None
        
    @staticmethod
    def _download_pdf(url: str, settings: Settings, pdf_save_path: Path):
        temp_scraper = WebScraper(settings, loguru.logger)
        temp_scraper.download_file(url, pdf_save_path)
        temp_scraper.close()
        return pdf_save_path

    @staticmethod
    def _get_abstract_from_conference_website(url: str, settings_dict: dict):
        logger = loguru.logger
        settings = Settings.from_dict(settings_dict)
        temp_scraper = WebScraper(settings, logger)

        temp_scraper.fetch_url(url)
        abstract = None

        if 'openaccess.thecvf.com' in url:
            abstract = temp_scraper.find_element_by_id('abstract').text
        elif 'cvpr.thecvf.com' in url:
            abstract = temp_scraper.find_element_by_id('abstractExample').text
        elif 'iclr.cc' in url:
            temp_scraper.click_element_by_classname('card-link')
            elements = temp_scraper.find_element('div', {'id': 'abstractExample'})
            if len(elements) > 0:
                abstract_p = elements[0].find('p')
                if abstract_p is not None:
                    abstract = abstract_p.text
                else:
                    abstract = elements[0].text.replace('Abstract:', '').strip()
        elif 'openreview.net' in url:
            elements = temp_scraper.find_element('div', {'class': 'note-content-value markdown-rendered'})
            if len(elements) > 0:
                abstract_p = elements[0].find('p')
                if abstract_p is not None:
                    abstract = abstract_p.text
                else:
                    abstract = elements[0].text.replace('Abstract:', '').strip()

        temp_scraper.close()
        if abstract is None:
            logger.warning(f'failed to get abstract for {url}')
        return abstract
        
    @staticmethod
    def _scrape_paper_info_papercopilot_single(row_in_raw_data: tuple, settings_dict: dict, conference_name: str, year: int, mandatory_keywords: list[str], additional_keywords: list[str]):
        # Reconstruct settings and logger within the worker process
        from sotapapers.core.settings import Settings
        from sotapapers.core.database import DataBase
        from sotapapers.modules.web_scraper import WebScraper
        from sotapapers.modules.arxiv_client import ArxivClient
        from sotapapers.modules.semantic_scholar_client import SemanticScholarClient
        from sotapapers.modules.github_repo_searcher import GitHubRepoSearcher
        from sotapapers.modules.paper_reader import PaperReader
        from sotapapers.core.paper import PaperDataDump
        import loguru
        from pathlib import Path
        import os

        settings = Settings.from_dict(settings_dict)
        
        log = loguru.logger.bind(process_id=os.getpid())
        log.remove()
        log.add(sys.stderr, level=settings.config.paper_crawler.log_level)

        arxiv_client = ArxivClient(settings, log)
        scholarly_client = SemanticScholarClient(settings, log)
        github_repo_searcher = GitHubRepoSearcher(settings, log)
        paper_data_dump = PaperDataDump(log)
        temp_web_scraper = WebScraper(settings, log, request_timeout=settings.config.paper_crawler.request_timeout)
        db = DataBase(settings.config.database.url, log)

        try:
            title, url, conf_url, abstract, authors_list, affiliations_list, affiliations_country_list, session_type, citations, pdf_url, youtube_url, github_url, project_page_url, arxiv_url = row_in_raw_data
            paper = PaperCrawler._scrape_paper_info_papercopilot(settings, log, conference_name, mandatory_keywords, additional_keywords, title, url, abstract, year, authors_list, affiliations_list, affiliations_country_list, session_type, citations, pdf_url, youtube_url, github_url, project_page_url, arxiv_url, temp_web_scraper)
            if paper is None:
                log.warning(f'failed to scrape paper info for {title}')
                return None
            
            if paper.arxiv_id is None and paper.media.arxiv_url is None:
                # Try to get arxiv_id and arxiv_url using arxiv_client if not available from initial scrape
                arxiv_paper = arxiv_client.search_by_title(paper.title)
                if arxiv_paper:
                    paper.arxiv_id = arxiv_paper.arxiv_id
                    paper.media.arxiv_url = arxiv_paper.media.arxiv_url

            PaperCrawler._update_paper_metrics(paper, arxiv_client, scholarly_client, github_repo_searcher, log)

            # Additional scraping for abstract, references, and citing papers
            if paper.media.pdf_url:
                pdf_save_dir = Path(f'{settings.config.paper_crawler.pdf_download_basepath}/conference/{conference_name}/{year}')
                pdf_save_dir.mkdir(parents=True, exist_ok=True)

                pdf_save_path = pdf_save_dir / f'{paper.title}.pdf'

                # Use the worker's own web_scraper instance
                temp_web_scraper.download_file(paper.media.pdf_url, pdf_save_path)

            paper_data_dump.dump(paper)

            # Add paper to DB
            db.insert_paper(paper)
            # db.dispose() # Dispose DB connection after use (this should be handled by context manager or outer scope for long-running connections if not per-paper)
            
            # backward recursive crawling
            PaperCrawler._grab_reference_papers(log, db, paper, int(year), mandatory_keywords, additional_keywords, settings.config.paper_crawler.backward_recursive_depth)

            # forward recursive crawling
            PaperCrawler._grab_citing_papers(log, db, paper, int(year), mandatory_keywords, additional_keywords, settings.config.paper_crawler.forward_recursive_depth)
            return paper

        except Exception as e:
            log.error(f"Error downloading or processing paper: {e}")
            return None
        
        finally:
            # Ensure the WebScraper's driver is quit when the task is done
            if temp_web_scraper is not None:
                temp_web_scraper.close()
            if db is not None:
                db.dispose()

    @staticmethod
    def _scrape_paper_info_papercopilot(settings: Settings, logger, conference_name: str, mandatory_keywords: list[str], additional_keywords: list[str], title, url, abstract, year, authors_list, affiliations_list, affiliations_country_list, session_type, citations, pdf_url, youtube_url, github_url, project_page_url, arxiv_url, web_scraper: WebScraper = None):
        # Use passed web_scraper instance or create a new one if not provided
        if abstract is None:
            logger.warning(f'failed to get abstract for paper: {title} (url: {url})')
            return None

        logger.debug(f'getting links for {title}')

        paper_reader = PaperReader(settings, logger)
        arxiv_client = ArxivClient(settings, loguru.logger)
        pdf_download_basepath = settings.config.paper_crawler.pdf_download_basepath
        references = None

        if pdf_url:
            try:
                pdf_url = pdf_url.replace('paper.html', 'paper.pdf')
                pdf_url = pdf_url.replace('html', 'papers')
                pdf_save_dir = Path(f'{pdf_download_basepath}/conference/{conference_name}/{year}')
                pdf_save_dir.mkdir(parents=True, exist_ok=True)
                pdf_save_path = pdf_save_dir / f'{title}.pdf'
               
                if not pdf_save_path.exists():
                    logger.debug(f'downloading pdf for {title}: {pdf_url}')
                    PaperCrawler._download_pdf(pdf_url, settings, pdf_save_path)

                paper_reader.set_file_path(pdf_save_path)
                references = paper_reader.extract_references()

                for ref in references:
                    matched_keywords = [keyword for keyword in mandatory_keywords if keyword.lower() in ref.title.lower().split(' ')]
                    matched_additional_keywords = [keyword for keyword in additional_keywords if keyword.lower() in ref.content.abstract.lower().split(' ')]

                    if len(matched_keywords) < len(mandatory_keywords) / 2.0 or len(matched_additional_keywords) < len(additional_keywords) / 4.0:
                        continue

                    if ref.arxiv_id is not None:
                        ref_arxiv_paper = arxiv_client.search_by_id(ref.arxiv_id)
                    else:
                        ref_arxiv_paper = arxiv_client.search_by_title(ref.title)
                    
                    if ref_arxiv_paper is not None:
                        ref.arxiv_id = ref_arxiv_paper.arxiv_id
                        ref.media.arxiv_url = ref_arxiv_paper.media.arxiv_url
                        ref.year = ref_arxiv_paper.year
                        if ref.content.abstract is None:
                            ref.content.abstract = ref_arxiv_paper.content.abstract
                        if ref.content.bibtex is None:
                            ref.content.bibtex = ref_arxiv_paper.content.bibtex

            except Exception as e:
                logger.error(f'An error occurred while extracting references: {str(e)}')

        extract_using_llm = False

        primary_task = None
        secondary_task = None
        tertiary_task = None
        primary_method = None
        secondary_method = None
        tertiary_method = None
        datasets_used = []
        metrics_used = []
        comparisons = {}
        limitations = None
        
        if extract_using_llm:
            tasks = paper_reader.extract_tasks()
            primary_task = tasks[0]
            secondary_task = tasks[1]
            tertiary_task = tasks[2]
            
            methods = paper_reader.extract_methods()
            primary_method = paper_reader.summarize_sentence(methods[0], settings.get('paper_reader').llm.max_summary_words_normal)
            secondary_method = paper_reader.summarize_sentence(methods[1], settings.get('paper_reader').llm.max_summary_words_normal)
            tertiary_method = paper_reader.summarize_sentence(methods[2], settings.get('paper_reader').llm.max_summary_words_normal)
            
            datasets_used, metrics_used, comparisons_list = paper_reader.extract_datasets_and_metrics()
            comparisons = {}
            
            for comparison_dict in comparisons_list:
                if 'reference_index' not in comparison_dict or 'judgement_result' not in comparison_dict:
                    continue
                
                reference_index_str = comparison_dict['reference_index']
                judgement_str = comparison_dict['judgement_result']
                
                try:
                    reference_index = int(reference_index_str)
                    if reference_index >= len(references):
                        logger.warning(f'reference index {reference_index} is out of range for {len(references)} references')
                        continue
                    
                    reference_paper = references[reference_index]

                    if judgement_str == 'outstanding':
                        judgement = PaperComparison.OUTSTANDING
                    elif judgement_str == 'even_better':
                        judgement = PaperComparison.EVEN_BETTER
                    elif judgement_str == 'better':
                        judgement = PaperComparison.BETTER
                    elif judgement_str == 'similar':
                        judgement = PaperComparison.SIMILAR
                    elif judgement_str == 'not_that_good':
                        judgement = PaperComparison.NOT_THAT_GOOD
                    else:
                        judgement = PaperComparison.UNKNOWN

                    comparisons[reference_paper.id] = judgement
                except Exception as e:
                    logger.error(f'An error occurred while extracting comparisons: {str(e)}')
                    continue
                
            limitations_str = paper_reader.extract_limitations()
            limitations = None

            if limitations_str is not None:
                limitations = paper_reader.summarize_paragraph(limitations_str, settings.get('paper_reader').llm.max_summary_sentences_normal)

            print(f'title: {title}')
            print(f'url: {url}')
            print(f'year: {year}')
            print(f'authors_list: {authors_list}')
            print(f'affiliations_list: {affiliations_list}')
            print(f'affiliations_country_list: {affiliations_country_list}')
            print(f'session_type: {session_type}')
            print(f'citations: {citations}')
            print(f'pdf_url: {pdf_url}')
            print(f'youtube_url: {youtube_url}')
            print(f'github_url: {github_url}')
            print(f'project_page_url: {project_page_url}')
            print(f'primary_task: {primary_task}')
            print(f'secondary_task: {secondary_task}')
            print(f'tertiary_task: {tertiary_task}')
            print(f'primary_method: {primary_method}')
            print(f'secondary_method: {secondary_method}')
            print(f'tertiary_method: {tertiary_method}')
            print(f'datasets_used: {datasets_used}')
            print(f'metrics_used: {metrics_used}')
            print(f'comparisons: {comparisons}')
            print(f'limitations: {limitations}')

        paper_content = PaperContent(
            abstract=abstract,
            references=references,
            cited_by=None,
            bibtex=None,
            primary_task=primary_task,
            secondary_task=secondary_task,
            tertiary_task=tertiary_task,
            primary_method=primary_method,
            secondary_method=secondary_method,
            tertiary_method=tertiary_method,
            datasets_used=datasets_used,
            metrics_used=metrics_used,
            comparisons=comparisons,
            limitations=limitations
        )
        
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
        citations_total = citations if isinstance(citations, int) else None

        paper_metrics = PaperMetrics(
            github_star_count=github_star_count,
            github_star_avg_hype=github_star_avg_hype,
            github_star_weekly_hype=github_star_weekly_hype,
            github_star_monthly_hype=github_star_monthly_hype,
            github_star_tracking_start_date=github_star_tracking_start_date,
            github_star_tracking_latest_footprint=github_star_tracking_latest_footprint,
            citations_total=citations_total
        )

        paper_type = PaperType.CONFERENCE_PAPER
        paper_session_type = PaperSessionType.UNKNOWN
        paper_accept_status = PaperAcceptStatus.NORMAL

        if session_type == 'Highlight' or session_type == 'Spotlight':
            paper_session_type = PaperSessionType.ORAL
            paper_accept_status = PaperAcceptStatus.HILIGHTED
        elif session_type == 'Oral':
            paper_session_type = PaperSessionType.ORAL
        elif session_type == 'Poster':
            paper_session_type = PaperSessionType.POSTER
        elif session_type == 'Award Candidate':
            paper_accept_status = PaperAcceptStatus.AWARD_CANDIDATE
        elif session_type == 'Best Paper':
            paper_accept_status = PaperAcceptStatus.BEST_PAPER_AWARD

        arxiv_id = arxiv_url.split('/')[-1] if arxiv_url is not None else None
        
        paper = Paper(
            id=make_generated_id(title, year),
            arxiv_id=arxiv_id,
            title=title,
            authors=authors_list,
            affiliations=affiliations_list,
            affiliations_country=affiliations_country_list,
            year=year,
            venue=conference_name,
            pages=None,
            paper_type=paper_type,
            session_type=paper_session_type,
            accept_status=paper_accept_status,
            note=None,
            content=paper_content,
            media=paper_media,
            metrics=paper_metrics
        )
        return paper

if __name__ == "__main__":
    mp.set_start_method('spawn')
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--config-path', type=str, default=get_config_path().absolute())
    parser.add_argument('--mode', type=str, default='keyword_search')
    parser.add_argument('--keywords', type=str, nargs='+', default=[])
    parser.add_argument('--additional-keywords', type=str, nargs='+', default=[])
    args = parser.parse_args()

    config_path = Path(args.config_path)
    settings = Settings(config_path)
    logger = loguru.logger

    if args.mode == 'conference_papers':
        settings.mode = CrawlMode.CONFERENCE_PAPERS
    elif args.mode == 'keyword_search':
        settings.mode = CrawlMode.KEYWORD_SEARCH
    else:
        raise ValueError(f'Invalid mode: {args.mode}')

    paper_crawler = PaperCrawler(settings, logger)
    try:
        paper_crawler.run(keywords=args.keywords)
    finally:
        pass
    