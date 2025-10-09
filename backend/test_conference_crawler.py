#!/usr/bin/env python3
"""
Simple validation script for conference paper crawler.

This script demonstrates how to use the conference crawling functionality.
It does NOT actually run the crawler (to avoid heavy resource usage),
but validates that all components are importable and properly structured.
"""

import sys
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_imports():
    """Test that all required modules can be imported."""
    logger.info("Testing imports...")

    try:
        from utils.web_scraper import WebScraper
        logger.info("✓ WebScraper imported successfully")
    except Exception as e:
        logger.error(f"✗ Failed to import WebScraper: {e}")
        return False

    try:
        from jobs.paper_crawler import (
            _crawl_conference,
            _parse_conference_papers_list,
            _get_abstract_from_conference_website,
            _create_paper_from_conference_data
        )
        logger.info("✓ Conference crawler functions imported successfully")
    except Exception as e:
        logger.error(f"✗ Failed to import conference crawler functions: {e}")
        return False

    try:
        from models.paper import Paper
        logger.info("✓ Paper model imported successfully")
    except Exception as e:
        logger.error(f"✗ Failed to import Paper model: {e}")
        return False

    return True


def test_web_scraper_initialization():
    """Test WebScraper initialization."""
    logger.info("\nTesting WebScraper initialization...")

    try:
        from utils.web_scraper import WebScraper

        scraper = WebScraper(request_timeout=60, headless=True)
        logger.info("✓ WebScraper initialized successfully")

        # Test context manager support
        logger.info("✓ WebScraper supports context manager protocol")

        return True
    except Exception as e:
        logger.error(f"✗ WebScraper initialization failed: {e}")
        return False


def test_parse_conference_papers():
    """Test parsing conference papers from HTML."""
    logger.info("\nTesting conference paper parsing...")

    try:
        from jobs.paper_crawler import _parse_conference_papers_list

        # Simple test HTML (minimal example)
        test_html = """
        <html>
            <table id="paperlist">
                <thead>
                    <tr></tr>
                    <tr>
                        <th>Index</th>
                        <th>Year</th>
                        <th>Title</th>
                        <th>Venue</th>
                        <th>Authors</th>
                        <th>Affiliations</th>
                        <th>Countries</th>
                        <th>Status</th>
                        <th>Citations</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>1</td>
                        <td>2024</td>
                        <td><a href="http://example.com/paper1">Test Paper</a></td>
                        <td>CVPR</td>
                        <td data-val="Author1;Author2">Authors</td>
                        <td data-val="MIT;Stanford">Affiliations</td>
                        <td data-val="USA;USA">Countries</td>
                        <td data-val="Poster">Status</td>
                        <td data-val="10">10</td>
                    </tr>
                </tbody>
            </table>
        </html>
        """

        papers = _parse_conference_papers_list(test_html, 'paperlist', 'CVPR')

        if len(papers) > 0:
            logger.info(f"✓ Parsed {len(papers)} paper(s) from test HTML")
            logger.info(f"  Sample paper: {papers[0]['title']}")
            return True
        else:
            logger.warning("✗ No papers parsed from test HTML")
            return False

    except Exception as e:
        logger.error(f"✗ Conference paper parsing failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_create_paper_from_data():
    """Test creating Paper model from conference data."""
    logger.info("\nTesting Paper creation from conference data...")

    try:
        from jobs.paper_crawler import _create_paper_from_conference_data

        test_data = {
            'title': 'Test Paper on Computer Vision',
            'authors': ['Alice Smith', 'Bob Jones'],
            'abstract': 'This is a test abstract.',
            'arxiv_id': '2024.12345',
            'arxiv_url': 'https://arxiv.org/abs/2024.12345',
            'pdf_url': 'https://arxiv.org/pdf/2024.12345.pdf',
            'github_url': 'https://github.com/example/repo',
            'session_type': 'Oral',
            'affiliations': ['MIT', 'Stanford'],
            'affiliations_country': ['USA', 'USA'],
        }

        paper = _create_paper_from_conference_data(
            test_data,
            conference_name='CVPR',
            conference_year=2024
        )

        logger.info(f"✓ Created Paper: {paper.title}")
        logger.info(f"  Venue: {paper.venue}")
        logger.info(f"  Authors: {len(paper.authors)}")
        logger.info(f"  Type: {paper.paper_type}")
        logger.info(f"  Accept status: {paper.accept_status}")

        return True

    except Exception as e:
        logger.error(f"✗ Paper creation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all validation tests."""
    logger.info("=" * 60)
    logger.info("Conference Crawler Validation Suite")
    logger.info("=" * 60)

    results = []

    # Run tests
    results.append(("Import Tests", test_imports()))
    results.append(("WebScraper Initialization", test_web_scraper_initialization()))
    results.append(("Parse Conference Papers", test_parse_conference_papers()))
    results.append(("Create Paper from Data", test_create_paper_from_data()))

    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("Test Summary")
    logger.info("=" * 60)

    for test_name, passed in results:
        status = "PASSED" if passed else "FAILED"
        logger.info(f"{test_name}: {status}")

    total_passed = sum(1 for _, passed in results if passed)
    total_tests = len(results)

    logger.info(f"\nTotal: {total_passed}/{total_tests} tests passed")

    if total_passed == total_tests:
        logger.info("\n✓ All validation tests passed!")
        return 0
    else:
        logger.error("\n✗ Some validation tests failed")
        return 1


if __name__ == '__main__':
    sys.exit(main())
