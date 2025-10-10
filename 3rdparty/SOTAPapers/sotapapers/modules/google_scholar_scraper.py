import loguru
import time
import random

from urllib.parse import quote_plus
from selenium.webdriver.common.by import By
from pathlib import Path

from sotapapers.core.schemas import PaperType, PaperSessionType, PaperAcceptStatus
from sotapapers.core.settings import Settings
from sotapapers.core.paper import Paper
from sotapapers.modules.arxiv_client import ArxivClient
from sotapapers.modules.web_scraper import WebScraper
from sotapapers.modules.paper_search_client import PaperSearchClient

from bs4 import BeautifulSoup


class GoogleScholarScraper:
    def __init__(self, settings: Settings, logger: loguru.logger):
        self.settings = settings
        self.logger = logger
        self.web_scraper = WebScraper(settings, logger)
        self.arxiv_client = ArxivClient(settings, logger)

    def search_citing_papers(self, paper: Paper) -> list[Paper]:
        data = []
        # make query string url-safe
        url = f'https://scholar.google.com/scholar?hl=en&as_sdt=0%2C5&q={quote_plus(paper.title.lower())}&btnG=&oq=at'
        #url = f"https://scholar.google.com/scholar?q={quote_plus(paper.title)}&hl=en&as_sdt=0,5"
        
        NUM_OF_PAGES = 1
        page_index = 0
        
        for _ in range(NUM_OF_PAGES):
            page_url = self.get_url_for_page(url, page_index)
            entries = self.get_data_from_page(page_url)
            data.extend(entries)
            page_index += 10

        for entry in data:
            if entry['citations'] is None:
                continue
            for citation in entry['citations']:
                self.logger.debug(f'searching for citing paper: {citation["title"]}')
                arxiv_paper = self.arxiv_client.search_by_title(citation['title'])
                if arxiv_paper is not None:
                    paper.content.cited_by.append(arxiv_paper)

    def get_citations(self, article_id):
        url = f"https://scholar.google.com/scholar?q=info:{article_id}:scholar.google.com&output=cite"
        self.web_scraper.fetch_url(url)

        html = self.web_scraper.driver.page_source
        soup = BeautifulSoup(html, "html.parser")
        data = []
        for citation in soup.find_all("tr"):
            title = citation.find("th", {"class": "gs_cith"}).get_text(strip=True)
            content = citation.find("div", {"class": "gs_citr"}).get_text(strip=True)
            entry = {
                "title": title,
                "content": content,
            }
            data.append(entry)
        return data

    def parse_data_from_article(self, article):
        self.logger.debug(f'parsing article: {article}')
        
        title_elem = article.find("h3", {"class": "gs_rt"})
        title = title_elem.get_text()
        title_anchor_elem = article.select("a")[0]
        url = title_anchor_elem["href"]
        article_id = title_anchor_elem["id"]
        authors = article.find("div", {"class": "gs_a"}).get_text()
        return {
            "title": title,
            "authors": authors,
            "url": url,
            "citations": self.get_citations(article_id),
        }

    def get_url_for_page(self, url, page_index):
        return url# + f"&start={page_index}"

    def get_data_from_page(self, url):
        # sleep randomly
        time.sleep(random.uniform(0.5, 1.5))
        
        self.web_scraper.fetch_url(url)
        time.sleep(random.uniform(0.5, 1.5))

        #if not self.web_scraper._wait_for_element_located(By.CLASS_NAME, 'gs_ri', 5):
        #    return []

        html = self.web_scraper.current_page_source()
        soup = BeautifulSoup(html, "html.parser")

        if __name__ == "__main__":
            with open("google_scholar_output.html", "w") as f:
                f.write(soup.prettify())
        
        articles = soup.find_all("div", {"class": "gs_ri"})
        
        return [self.parse_data_from_article(article) for article in articles]

if __name__ == "__main__":
    # This is a test function for GoogleScholarScraper
    from sotapapers.core.schemas import Paper, PaperContent, PaperMedia, PaperMetrics # Import Paper schema

    settings = Settings(Path('sotapapers/configs'))
    logger = loguru.logger

    scraper = GoogleScholarScraper(settings, logger)

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

    logger.info(f"Searching for citing papers of: {dummy_paper.title}")
    scraper.search_citing_papers(dummy_paper)

    if dummy_paper.content.cited_by:
        logger.info(f"Found {len(dummy_paper.content.cited_by)} citing papers:")
        for cited_paper in dummy_paper.content.cited_by:
            logger.info(f"- {cited_paper.title} by {', '.join(cited_paper.authors)}")
    else:
        logger.info("No citing papers found for the dummy paper.")
