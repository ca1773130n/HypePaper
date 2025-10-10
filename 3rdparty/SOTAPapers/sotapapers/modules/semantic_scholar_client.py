import requests
import loguru

from sotapapers.core.settings import Settings
from sotapapers.core.schemas import Paper, PaperType, PaperMedia, PaperMetrics, PaperContent, PaperSessionType, PaperAcceptStatus
from sotapapers.modules.paper_search_client import PaperSearchClient
from sotapapers.utils.id_util import make_generated_id
from sotapapers.utils.url_utils import get_url_with_prefix
from sotapapers.utils.string_util import compare_strings_with_tolerance

from semanticscholar import SemanticScholar
from typing import List

class SemanticScholarClient(PaperSearchClient):
    def __init__(self, settings: Settings, logger: loguru.logger):
        self.settings = settings
        self.log = logger

        api_key = self.settings.config.paper_search_client.semantic_scholar.api_key
        if len(api_key) == 0:
            api_key = None

        self.api_key = api_key
        self.base_url = self.settings.config.paper_search_client.semantic_scholar.base_url
        self.max_limit = int(self.settings.config.paper_search_client.semantic_scholar.max_limit)
        self.client = SemanticScholar(api_key=api_key)

    def search(self, keyword: str) -> List[Paper]:
        try:
            search_result = self.client.search_paper(keyword, limit=self.max_limit)
            if not search_result:
                self.log.warning(f'No papers found for keyword: {keyword}')
                return []

            papers = []
            for paper in search_result:
                paper_object = self._make_paper_object(paper)
                papers.append(paper_object)
            return papers
        except Exception as e:
            self.log.error(f'An error occurred while searching for papers by keyword: {keyword}')
            return []

    def search_by_title(self, title: str) -> Paper:
        try:
            search_result = self.client.search_paper(title, match_title=True)
            if search_result is not None:
                paper_title = search_result.title
                if paper_title is None:
                    return None
                if not compare_strings_with_tolerance(paper_title, title):
                    return None
                paper_object = self._make_paper_object(search_result._data)
                return paper_object
            else:
                self.log.warning(f'No paper found for title: {title}')
                return None
        except Exception as e:
            self.log.error(f'An error occurred while searching for paper by title: {title}: {e}')
            return None

    def _make_paper_object(self, paper) -> Paper:
        paperId = paper.get('paperId')
        
        paper_title = paper.get('title')
        paper_year = paper.get('year')
        abstract = paper.get('abstract')

        if self.api_key:
            url = get_url_with_prefix(self.base_url, paperId, self.settings)
            query_params = {"fields": "title,year,abstract,citationCount,references,citations"}
            headers = {"x-api-key": self.api_key}
            response = requests.get(url, params=query_params, headers=headers)

            if response.status_code == 200:
                response_data = response.json()
                citations_data = response_data.get('citations')
                references_data = response_data.get('references')
                paper_bibtex = paper.get('citationStyles', {}).get('bibtex')
            else:
                self.log.error(f"Request failed with status code {response.status_code}: {response.text}")
                citations_data = None
                references_data = None
                paper_bibtex = None
        else:
            citations_data = None
            references_data = None
            paper_bibtex = paper.get('citationStyles', {}).get('bibtex')

        paper_venue_name = paper.get('venue') if paper.get('venue') is not None and len(paper.get('venue')) > 0 else None
        paper_pub_types = paper.get('publicationTypes')
        
        paper_type = PaperType.UNKNOWN
        paper_venue = None
        paper_arxiv_id = None

        external_ids = paper.get('externalIds')
        if paper_venue_name == 'arXiv.org' and external_ids is not None:
            paper_venue = 'arXiv'
            paper_arxiv_id = external_ids.get('ArXiv')
        else:
            if paper_pub_types is not None and len(paper_pub_types) > 0:
                paper_pub_type = paper_pub_types[0]
                if paper_pub_type == 'JournalArticle':
                    journal = paper.get('journal')
                    if journal is not None:
                        paper_venue_name = journal.get('name')
                        if paper_venue_name == 'ArXiv':
                            paper_venue = 'arXiv'
                            paper_arxiv_id = journal.get('volume')
                        else:
                            paper_venue = paper_venue_name
                            paper_type = PaperType.JOURNAL_PAPER
                else:
                    paper_type = PaperType.CONFERENCE_PAPER

        arxiv_url = None
        if paper_arxiv_id is not None:
            arxiv_url = f'https://arxiv.org/abs/{paper_arxiv_id}'

        paper_session_type = PaperSessionType.UNKNOWN
        paper_accept_status = PaperAcceptStatus.UNKNOWN
        paper_note = None

        cited_by_papers = []
        if citations_data:
            for citing_paper in citations_data:
                cited_by_papers.append(Paper(
                    id=make_generated_id(citing_paper.get('title'), citing_paper.get('year')),
                    title=citing_paper.get('title'),
                    authors=[author.get('name') for author in citing_paper.get('authors')],
                    year=citing_paper.get('year'),
                    venue=citing_paper.get('venue') if citing_paper.get('venue') is not None and len(citing_paper.get('venue')) > 0 else None,
                ))
        
        references_papers = []
        if references_data:
            for ref_paper in references_data:
                references_papers.append(Paper(
                    id=make_generated_id(ref_paper.get('title'), ref_paper.get('year')),
                    title=ref_paper.get('title'),
                    authors=[author.get('name') for author in ref_paper.get('authors')],
                    year=ref_paper.get('year'),
                    venue=ref_paper.get('venue') if ref_paper.get('venue') is not None and len(ref_paper.get('venue')) > 0 else None,
                ))

        paper_content = PaperContent(
            abstract=abstract,
            references=references_papers,
            cited_by=cited_by_papers,
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
        
        if paper.get('openAccessPdf') is not None:
            pdf_url = paper.get('openAccessPdf').get('url')
        else:
            pdf_url = None
        
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
        citations_total = paper.get('citationCount')
        
        paper_metrics = PaperMetrics(
            github_star_count=github_star_count,
            github_star_avg_hype=github_star_avg_hype,
            github_star_weekly_hype=github_star_weekly_hype,
            github_star_monthly_hype=github_star_monthly_hype,
            github_star_tracking_start_date=github_star_tracking_start_date,
            github_star_tracking_latest_footprint=github_star_tracking_latest_footprint,
            citations_total=citations_total
        )
        
        authors = [author.get('name') for author in paper.get('authors')]
        
        paper_object = Paper(
            id=make_generated_id(paper.get('title'), paper.get('year')),
            arxiv_id=paper_arxiv_id,
            title=paper_title,
            authors=authors,
            year=paper_year,
            venue=paper_venue,
            pages=None,
            paper_type=paper_type,
            session_type=paper_session_type,
            accept_status=paper_accept_status,
            note=paper_note,
            content=paper_content,
            media=paper_media,
            metrics=paper_metrics
        )
        
        return paper_object

    def search_by_paper_id(self, paper_id: str) -> Paper:
        try:
            paper_result = self.client.get_paper(paper_id, fields=['title', 'year', 'abstract', 'citationCount', 'references', 'citations', 'externalIds', 'url', 'publicationVenue', 'openAccessPdf', 'fieldsOfStudy', 's2FieldsOfStudy', 'publicationTypes', 'publicationDate', 'journal', 'citationStyles', 'authors', 'venue'])
            if paper_result:
                return self._make_paper_object(paper_result._data)
            else:
                self.log.warning(f'No paper found for ID: {paper_id}')
                return None
        except Exception as e:
            self.log.error(f'An error occurred while searching for paper by ID: {paper_id}: {e}')
            return None

    """ this is an example of response:
        {
            "paperId": "f22d78d06f6c603ab1c6e244db955e632f6d7af0",
            "externalIds": {
                "DBLP": "journals/corr/abs-2412-00678",
                "ArXiv": "2412.00678",
                "DOI": "10.48550/arXiv.2412.00678",
                "CorpusId": 274437761
            },
            "corpusId": 274437761,
            "publicationVenue": {
                "id": "1901e811-ee72-4b20-8f7e-de08cd395a10",
                "name": "arXiv.org",
                "alternate_names": [
                    "ArXiv"
                ],
                "issn": "2331-8422",
                "url": "https://arxiv.org"
            },
            "url": "https://www.semanticscholar.org/paper/f22d78d06f6c603ab1c6e244db955e632f6d7af0",
            "title": "2DMamba: Efficient State Space Model for Image Representation with Applications on Giga-Pixel Whole Slide Image Classification",
            "venue": "arXiv.org",
            "year": 2024,
            "referenceCount": 48,
            "citationCount": 5,
            "influentialCitationCount": 1,
            "isOpenAccess": false,
            "openAccessPdf": {
                "url": "",
                "status": null,
                "license": null,
                "disclaimer": "Notice: Paper or abstract available at https://arxiv.org/abs/2412.00678, which is subject to the license by the author or copyright owner provided with this content. Please go to the source to verify the license and copyright information for your use."
            },
            "fieldsOfStudy": [
                "Computer Science"
            ],
            "s2FieldsOfStudy": [
                {
                    "category": "Computer Science",
                    "source": "external"
                },
                {
                    "category": "Computer Science",
                    "source": "s2-fos-model"
                },
                {
                    "category": "Engineering",
                    "source": "s2-fos-model"
                },
                {
                    "category": "Environmental Science",
                    "source": "s2-fos-model"
                }
            ],
            "publicationTypes": [
                "JournalArticle"
            ],
            "publicationDate": "2024-12-01",
            "journal": {
                "name": "ArXiv",
                "volume": "abs/2412.00678"
            },
            "citationStyles": {
                "bibtex": "@Article{Zhang20242DMambaES,\n author = {Jingwei Zhang and Anh Tien Nguyen and Xi Han and Vincent Quoc-Huy Trinh and Hong Qin and Dimitris Samaras and Mahdi S. Hosseini},\n booktitle = {arXiv.org},\n journal = {ArXiv},\n title = {2DMamba: Efficient State Space Model for Image Representation with Applications on Giga-Pixel Whole Slide Image Classification},\n volume = {abs/2412.00678},\n year = {2024}\n}\n"
            },
            "authors": [
                {
                    "authorId": "2333520861",
                    "name": "Jingwei Zhang"
                },
                {
                    "authorId": "2333424272",
                    "name": "Anh Tien Nguyen"
                },
                {
                    "authorId": "2334226564",
                    "name": "Xi Han"
                },
                {
                    "authorId": "2280272719",
                    "name": "Vincent Quoc-Huy Trinh"
                },
                {
                    "authorId": "2333415743",
                    "name": "Hong Qin"
                },
                {
                    "authorId": "2280272169",
                    "name": "Dimitris Samaras"
                },
                {
                    "authorId": "2297772093",
                    "name": "Mahdi S. Hosseini"
                }
            ],
            "abstract": "Efficiently modeling large 2D contexts is essential for various fields including Giga-Pixel Whole Slide Imaging (WSI) and remote sensing. Transformer-based models offer high parallelism but face challenges due to their quadratic complexity for handling long sequences. Recently, Mamba introduced a selective State Space Model (SSM) with linear complexity and high parallelism, enabling effective and efficient modeling of wide context in 1D sequences. However, extending Mamba to vision tasks, which inherently involve 2D structures, results in spatial discrepancies due to the limitations of 1D sequence processing. On the other hand, current 2D SSMs inherently model 2D structures but they suffer from prohibitively slow computation due to the lack of efficient parallel algorithms. In this work, we propose 2DMamba, a novel 2D selective SSM framework that incorporates the 2D spatial structure of images into Mamba, with a highly optimized hardware-aware operator, adopting both spatial continuity and computational efficiency. We validate the versatility of our approach on both WSIs and natural images. Extensive experiments on 10 public datasets for WSI classification and survival analysis show that 2DMamba improves up to 2.48% in AUC, 3.11% in F1 score, 2.47% in accuracy and 5.52% in C-index. Additionally, integrating our method with VMamba for natural imaging yields 0.5 to 0.7 improvements in mIoU on the ADE20k semantic segmentation dataset, and 0.2% accuracy improvement on ImageNet-1K classification dataset. Our code is available at https://github.com/AtlasAnalyticsLab/2DMamba.",
            "matchScore": 351.5915
        }
        """ 