"""
Web scraping utilities for conference paper crawling.

Adapted from SOTAPapers WebScraper module with async support.
"""
import asyncio
import itertools
import logging
import random
from pathlib import Path
from time import sleep
from typing import Optional

import requests
import undetected_chromedriver as uc
from bs4 import BeautifulSoup
from selenium.common.exceptions import (
    ElementClickInterceptedException,
    NoSuchElementException,
    WebDriverException,
)
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


logger = logging.getLogger(__name__)


# User Agent rotation for anti-bot detection
def user_agent_rotator(user_agent_list):
    """Shuffle and rotate User Agent list."""
    random.shuffle(user_agent_list)
    return itertools.cycle(user_agent_list)


USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
]


def install_chrome_driver(headless: bool = True):
    """Install and configure Chrome driver with options."""
    options = uc.ChromeOptions()
    options.headless = headless

    user_agent_cycle = user_agent_rotator(USER_AGENTS)
    options.add_argument(f"--user-agent={next(user_agent_cycle)}")

    return options


class WebScraper:
    """
    Web scraper using Selenium with undetected ChromeDriver.

    Adapted from SOTAPapers for async/await architecture.
    """

    def __init__(self, request_timeout: int = 300, headless: bool = True):
        """
        Initialize WebScraper.

        Args:
            request_timeout: Timeout for HTTP requests in seconds
            headless: Run browser in headless mode
        """
        self.request_timeout = request_timeout
        self.headless = headless
        self.driver = None

    def open(self):
        """Open and initialize the Chrome driver."""
        if self.driver is not None:
            logger.warning("Driver already initialized, closing existing driver")
            self.close()

        try:
            driver_options = install_chrome_driver(headless=self.headless)
            self.driver = uc.Chrome(options=driver_options, use_subprocess=False)
            logger.info("ChromeDriver initialized successfully")
        except WebDriverException as e:
            logger.error(f"WebDriverException during initial driver setup: {e}")
            try:
                # Retry without use_subprocess
                self.driver = uc.Chrome(options=driver_options)
                logger.info("ChromeDriver re-initialized after initial failure")
            except Exception as retry_e:
                logger.critical(f"Failed to initialize ChromeDriver after retry: {retry_e}")
                self.driver = None
        except Exception as e:
            logger.critical(f"Unexpected error during ChromeDriver setup: {e}")
            self.driver = None

    def close(self):
        """Close the Chrome driver and clean up resources."""
        if hasattr(self, 'driver') and self.driver is not None:
            try:
                self.driver.quit()
                logger.debug("ChromeDriver closed successfully")
            except Exception as e:
                logger.warning(f"Error while quitting ChromeDriver: {e}")
            finally:
                self.driver = None

    def fetch_url(self, url: str, save_path: Optional[Path] = None, stream: bool = False):
        """
        Fetch a URL using the Chrome driver.

        Args:
            url: URL to fetch
            save_path: Optional path to save downloaded content
            stream: Whether to stream the download
        """
        if self.driver is None:
            logger.error("WebScraper is not initialized. Call open() first.")
            return

        logger.debug(f"Fetching URL: {url}")

        if save_path is not None and stream:
            self.download_file(url, save_path)
            return

        try:
            self.driver.get(url)
            self._wait_for_page_load()
            logger.debug(f"Page loaded: {url}")
        except Exception as e:
            logger.error(f"Failed to fetch URL: {url} (error: {e})")

    def current_page_source(self) -> str:
        """Get the current page source HTML."""
        if self.driver is None:
            return ""
        return self.driver.page_source

    def _wait_for_page_load(self, timeout: int = 10) -> bool:
        """
        Wait for page to finish loading.

        Args:
            timeout: Maximum wait time in seconds

        Returns:
            True if page loaded, False otherwise
        """
        try:
            WebDriverWait(self.driver, timeout).until(
                lambda d: d.execute_script('return document.readyState') == 'complete'
            )
            return True
        except Exception as e:
            logger.error(f"Failed to wait for page load: {e}")
            return False

    def _wait_for_element_located(self, by: By, value: str, timeout: int = 10) -> bool:
        """
        Wait for an element to be located on the page.

        Args:
            by: Selenium By locator type
            value: Locator value
            timeout: Maximum wait time in seconds

        Returns:
            True if element found, False otherwise
        """
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, value))
            )
            return True
        except Exception as e:
            logger.error(f"Failed to wait for element: {by} {value} (error: {e})")
            return False

    def _wait_for_element_clickable(self, by: By, value: str, timeout: int = 10):
        """
        Wait for an element to be clickable.

        Args:
            by: Selenium By locator type
            value: Locator value
            timeout: Maximum wait time in seconds

        Returns:
            Element if found and clickable, None otherwise
        """
        try:
            return WebDriverWait(self.driver, timeout).until(
                EC.element_to_be_clickable((by, value))
            )
        except Exception as e:
            logger.error(f"Failed to wait for element clickable: {by} {value} (error: {e})")
            return None

    def find_element_by_id(self, element_id: str):
        """Find element by ID."""
        return self._find_element(By.ID, element_id)

    def find_element_by_classname(self, classname: str):
        """Find element by class name."""
        return self._find_element(By.CLASS_NAME, classname)

    def _find_element(self, by: By, value: str):
        """
        Find element using Selenium.

        Args:
            by: Selenium By locator type
            value: Locator value

        Returns:
            Element if found, None otherwise
        """
        try:
            return self.driver.find_element(by, value)
        except NoSuchElementException:
            logger.error(f"NoSuchElementException: {by} {value}")
            return None

    def find_element(self, element_type: str, element_options_dict: dict):
        """
        Find elements in current page using BeautifulSoup.

        Args:
            element_type: HTML element type (e.g., 'div', 'table')
            element_options_dict: Dictionary of attributes to match

        Returns:
            List of matching elements
        """
        html = self.current_page_source()
        soup = BeautifulSoup(html, 'html.parser')
        return soup.find_all(element_type, element_options_dict)

    def get_table_from_html(self, html: str, table_id: str):
        """
        Extract table from HTML by ID.

        Args:
            html: HTML content
            table_id: Table element ID

        Returns:
            BeautifulSoup table element
        """
        soup = BeautifulSoup(html, 'html.parser')
        return soup.find('table', {'id': table_id})

    def click_element_by_id(
        self,
        element_id: str,
        wait_timeout: int = 30,
        max_attempts: int = 3,
        sleep_sec: int = 5
    ):
        """
        Click an element by ID.

        Args:
            element_id: Element ID
            wait_timeout: Maximum wait time for element
            max_attempts: Maximum retry attempts
            sleep_sec: Sleep time between retries
        """
        return self._click_element(By.ID, element_id, wait_timeout, max_attempts, sleep_sec)

    def click_element_by_classname(
        self,
        classname: str,
        wait_timeout: int = 30,
        max_attempts: int = 3,
        sleep_sec: int = 5
    ):
        """
        Click an element by class name.

        Args:
            classname: Element class name
            wait_timeout: Maximum wait time for element
            max_attempts: Maximum retry attempts
            sleep_sec: Sleep time between retries
        """
        return self._click_element(By.CLASS_NAME, classname, wait_timeout, max_attempts, sleep_sec)

    def _click_element(
        self,
        by: By,
        value: str,
        wait_timeout: int = 30,
        max_attempts: int = 3,
        sleep_sec: int = 5
    ):
        """
        Click an element with retry logic.

        Args:
            by: Selenium By locator type
            value: Locator value
            wait_timeout: Maximum wait time for element
            max_attempts: Maximum retry attempts
            sleep_sec: Sleep time between retries
        """
        if self.driver is None:
            self.open()

        for attempt in range(max_attempts):
            try:
                if self._wait_for_element_located(by, value, wait_timeout):
                    break
            except Exception as e:
                logger.warning(
                    f"Element [{value}] not located yet, retrying... "
                    f"(Attempt {attempt + 1}, sleeping {sleep_sec} sec)"
                )
                sleep(sleep_sec)
                sleep_sec *= 1.5

        element = self.driver.find_element(by, value)
        self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
        self.driver.execute_script("arguments[0].click();", element)

    def download_file(self, url: str, save_path: Path):
        """
        Download a file from URL.

        Args:
            url: URL to download from
            save_path: Path to save the file
        """
        try:
            response = requests.get(url, stream=True, timeout=self.request_timeout)
            if response.status_code == 200:
                save_path.parent.mkdir(parents=True, exist_ok=True)
                with open(save_path, 'wb') as file:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            file.write(chunk)
                logger.info(f"File downloaded successfully to {save_path}")
            else:
                logger.error(
                    f"Failed to fetch content from {url} "
                    f"(status code: {response.status_code})"
                )
        except Exception as e:
            logger.error(f"Error downloading file from {url}: {e}")

    def __enter__(self):
        """Context manager entry."""
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
