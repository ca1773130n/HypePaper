# Conference Paper Crawler Implementation Summary

## Overview

Successfully ported conference paper crawling functionality from `3rdparty/SOTAPapers` to `backend/src/jobs/paper_crawler.py` with the following key features:

- **Web Scraping**: Selenium-based scraping using undetected ChromeDriver
- **Conference Support**: CVPR and ICLR conferences from PaperCopilot tables
- **Async Architecture**: Adapted to work with AsyncSession and async/await patterns
- **Data Extraction**: Title, authors, abstract, PDF URL, GitHub URL, ArXiv URL, session type, citations

## Implementation Details

### 1. Dependencies Added (`backend/requirements.txt`)

```python
# Web scraping dependencies
selenium==4.15.2
beautifulsoup4==4.12.2
undetected-chromedriver==3.5.4
requests==2.31.0
```

### 2. WebScraper Utility (`backend/src/utils/web_scraper.py`)

Created a new `WebScraper` class adapted from SOTAPapers with:

- **Undetected ChromeDriver**: Bypasses anti-bot detection
- **User Agent Rotation**: Random user agent selection
- **Context Manager Support**: Automatic resource cleanup
- **Element Finding**: By ID, class name, or custom criteria
- **File Downloads**: Support for PDF downloads
- **BeautifulSoup Integration**: HTML parsing capabilities

Key methods:
- `open()`: Initialize Chrome driver
- `close()`: Clean up resources
- `fetch_url(url)`: Load a webpage
- `click_element_by_id(element_id)`: Click button/link
- `find_element(element_type, attributes)`: Parse HTML elements
- `get_table_from_html(html, table_id)`: Extract tables
- `download_file(url, save_path)`: Download files

### 3. Conference Crawler (`backend/src/jobs/paper_crawler.py`)

Implemented `_crawl_conference()` function with the following workflow:

```
1. Validate inputs (conference_name, conference_url, conference_year)
2. Open conference page with Selenium
3. Click "Fetch All" button to load all papers
4. Wait for dynamic content to load
5. Parse paper list from HTML table
6. For each paper:
   - Extract metadata from table row
   - Fetch abstract from conference webpage
   - Check for duplicates (by arxiv_id or title similarity)
   - Create Paper model instance
   - Store in database
7. Return (papers_discovered, papers_stored)
```

### 4. Helper Functions

#### `_parse_conference_papers_list(html, table_id, conference_name)`

Parses PaperCopilot HTML table and extracts:
- Title and URL
- Authors list
- Affiliations and countries
- Session type (Oral, Poster, Highlight, etc.)
- Citation count
- Social links (PDF, GitHub, ArXiv, YouTube, Project Page)

Returns list of paper data dictionaries.

#### `_get_abstract_from_conference_website(url, conference_name)`

Fetches abstract from conference-specific websites:
- **CVPR**: `openaccess.thecvf.com` or `cvpr.thecvf.com`
- **ICLR**: `iclr.cc` or `openreview.net`

Uses Selenium to navigate and BeautifulSoup to parse abstract text.

#### `_create_paper_from_conference_data(paper_data, conference_name, conference_year)`

Converts raw paper data to Paper model instance:
- Maps session types to paper_type and accept_status
- Creates affiliations dictionary
- Sets all metadata fields
- Returns Paper ORM object ready for database insertion

## Data Flow

```
PaperCopilot Table
    ↓
_parse_conference_papers_list()
    ↓
List of paper_data dicts
    ↓
_get_abstract_from_conference_website() (for each paper)
    ↓
Enhanced paper_data with abstract
    ↓
_create_paper_from_conference_data()
    ↓
Paper model instance
    ↓
Database storage (with duplicate detection)
```

## Conference Data Mapping

### Session Types → Paper Type & Accept Status

| Session Type     | Paper Type | Accept Status |
|------------------|------------|---------------|
| Highlight        | oral       | accepted      |
| Spotlight        | oral       | accepted      |
| Oral             | oral       | accepted      |
| Poster           | poster     | accepted      |
| Award Candidate  | -          | accepted      |
| Best Paper       | -          | accepted      |

### Extracted Fields

From PaperCopilot table:
- `title`: Paper title
- `authors`: List of author names
- `affiliations`: Author affiliations
- `affiliations_country`: Author countries
- `session_type`: Conference presentation type
- `citations`: Citation count from Google Scholar
- `pdf_url`: Direct PDF link
- `github_url`: GitHub repository
- `arxiv_url`: ArXiv page
- `arxiv_id`: ArXiv identifier
- `youtube_url`: Video presentation
- `project_page_url`: Project website

From conference webpage:
- `abstract`: Paper abstract text

## Usage Example

```python
from jobs.paper_crawler import crawl_papers

# Start conference crawl via Celery task
result = crawl_papers.delay(
    source='conference',
    conference_name='CVPR',
    conference_url='https://www.papercopilot.com/statistics/cvpr-statistics/',
    conference_year=2024
)

# Check result
result.ready()  # True when complete
result.get()    # Get result dict
```

## Architecture Adaptations

### SOTAPapers → HypePaper

1. **Database**: Sync → AsyncSession
   - Used `ThreadPoolExecutor` to run Selenium in separate thread
   - Async database operations in main event loop

2. **Paper Model**: Pydantic → SQLAlchemy ORM
   - Mapped PaperContent, PaperMedia, PaperMetrics to flat fields
   - Used JSONB for complex fields (affiliations, datasets, metrics)

3. **Multiprocessing**: Removed
   - Original used `multiprocessing.Pool` for parallel abstract fetching
   - Simplified to sequential processing (can be parallelized later)

4. **Settings**: Config file → Parameters
   - Changed from config-based to parameter-based invocation
   - More flexible for different conference sources

## Duplicate Detection

Papers are checked for duplicates using:

1. **ArXiv ID**: Exact match on `arxiv_id` field
2. **Title Similarity**: Using `rapidfuzz.fuzz.ratio()`
   - Threshold: 95% similarity
   - Only compared against same conference

## Error Handling

- Rejected papers are skipped (session_type contains "rejected")
- Papers without abstracts are logged as warnings
- Failed paper insertions are caught and logged
- Selenium errors are retried with exponential backoff

## Performance Considerations

- **Headless Browser**: Runs Chrome in headless mode for efficiency
- **Request Timeout**: 300 seconds for slow-loading pages
- **Wait Times**: 10 seconds after "Fetch All" button click
- **Thread Pool**: Runs Selenium in separate thread to avoid blocking async loop

## Testing

To test the implementation:

1. Install dependencies:
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

2. Run a conference crawl:
   ```python
   from jobs.paper_crawler import crawl_papers

   result = crawl_papers.delay(
       source='conference',
       conference_name='CVPR',
       conference_url='https://www.papercopilot.com/statistics/cvpr-statistics/',
       conference_year=2024
   )
   ```

3. Monitor progress via Celery task state updates

## Known Limitations

1. **Conference Support**: Only CVPR and ICLR currently supported
   - Can be extended by adding new URL patterns to `_get_abstract_from_conference_website()`

2. **Abstract Fetching**: Sequential (not parallelized)
   - Can be improved with multiprocessing or async HTTP

3. **ChromeDriver**: Requires Chrome browser installed
   - Undetected ChromeDriver handles installation automatically

4. **Rate Limiting**: No built-in rate limiting
   - May need to add delays for large-scale crawling

## Files Modified

1. **backend/requirements.txt**: Added web scraping dependencies
2. **backend/src/utils/web_scraper.py**: New WebScraper utility class
3. **backend/src/jobs/paper_crawler.py**:
   - Implemented `_crawl_conference()` function
   - Added helper functions for parsing and data creation

## Files Created

1. **backend/src/utils/web_scraper.py**: 370 lines
2. **backend/CONFERENCE_CRAWLER_IMPLEMENTATION.md**: This documentation

## Integration with Existing Code

The conference crawler integrates seamlessly with existing code:

- Uses existing `Paper` model from `backend/src/models/paper.py`
- Works with existing `AsyncSession` database connection
- Follows existing Celery task patterns
- Compatible with existing duplicate detection logic

## Next Steps

To use the conference crawler:

1. **Install Dependencies**:
   ```bash
   pip install -r backend/requirements.txt
   ```

2. **Start Celery Worker**:
   ```bash
   cd backend
   celery -A src.jobs.celery_app worker --loglevel=info
   ```

3. **Trigger Crawl**:
   ```python
   from src.jobs.paper_crawler import crawl_papers

   result = crawl_papers.delay(
       source='conference',
       conference_name='CVPR',
       conference_url='https://www.papercopilot.com/statistics/cvpr-statistics/',
       conference_year=2024
   )
   ```

## Maintenance

- Update ChromeDriver version in requirements.txt as needed
- Add new conference support by extending `_get_abstract_from_conference_website()`
- Monitor Selenium for breaking changes in PaperCopilot website structure
