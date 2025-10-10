import itertools
import os
import random
import loguru
import requests

from sotapapers.core.settings import Settings
from sotapapers.utils.url_utils import apply_url_prefix

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import ElementClickInterceptedException, NoSuchElementException, WebDriverException

from bs4 import BeautifulSoup

from pathlib import Path
from time import sleep
import time

# define a User Agent rotator
def user_agent_rotator(user_agent_list):
    # shuffle the User Agent list
    random.shuffle(user_agent_list)
    # rotate the shuffle to ensure all User Agents are used
    return itertools.cycle(user_agent_list)

# create a User Agent list
user_agents = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
]

def install_chrome_driver(logger: loguru.logger = None, max_attempts: int = 3, sleep_sec: int = 5):
    # Chromedriver is managed by undetected_chromedriver, so this function is simplified
    options = uc.ChromeOptions()
    options.headless = True

    user_agent_cycle = user_agent_rotator(user_agents)
    options.add_argument(f"--user-agent={next(user_agent_cycle)}")
    return options

class WebScraper:
    def __init__(self, settings: Settings, logger: loguru.logger, request_timeout: int = 300):
        self.settings = settings
        self.log = logger
        self.request_timeout = request_timeout
        self.driver = None # Initialize driver to None
        self.open()

    def open(self):
        try:
            driver_options = install_chrome_driver(logger=self.log)
            self.driver = uc.Chrome(options=driver_options, use_subprocess=False)
        except WebDriverException as e:
            self.log.error(f'WebDriverException during initial driver setup: {e}')
            try:
                self.driver = uc.Chrome(options=driver_options)
                self.log.info('Successfully re-initialized ChromeDriver after an initial failure.')
            except Exception as retry_e:
                self.log.critical(f'Failed to initialize ChromeDriver after retry: {retry_e}. Web scraping will not function.')
                self.driver = None # Ensure driver is None if retry also fails
        except Exception as e:
            self.log.critical(f'An unexpected error occurred during ChromeDriver setup: {e}. Web scraping will not function.')
            self.driver = None # Ensure driver is None for any other unexpected errors 

    def close(self):
        if hasattr(self, 'driver') and self.driver is not None:
            try:
                self.driver.quit()
            except Exception as e:
                self.log.warning(f"Error while quitting WebDriver: {e}")
            finally:
                self.driver = None

    def fetch_url(self, url, save_path: Path = None, stream: bool = False):
        if self.driver is None:
            self.log.error("WebScraper is not initialized. Cannot fetch URL.")
            return
        # Apply URL prefix
        url = apply_url_prefix(url, self.settings)
        self.log.debug(f'fetching url: {url}')
        
        if save_path is not None and stream:
            self.download_file(url, save_path)
            return

        try:
            self.driver.get(url)
            self._wait_for_page_load()
            self.log.debug(f'page loaded: {url}')
        except Exception as e:
            self.log.error(f'Failed to fetch url: {url} (error: {e})')
            return

    def set_html(self, html: str):
        script = f"document.body.innerHTML = `{html}`;"
        self.driver.execute_script(script)

    def current_page_source(self):
        return self.driver.page_source

    def _wait_for_page_load(self, timeout=10):
        try:
            WebDriverWait(self.driver, timeout).until(
                lambda d: d.execute_script('return document.readyState') == 'complete'
            )
        except Exception as e:
            self.log.error(f'Failed to wait for page load: {e}')
            return False
        return True
        
    def _wait_for_element_located(self, by, value, timeout=10):
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, value))
            )
        except Exception as e:
            self.log.error(f'Failed to wait for element located: {by} {value} (error: {e})')
            return False
        return True
        
    def _wait_for_element_disappear(self, element_id: str, timeout=10):
        element_locator = (By.ID, element_id)
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.invisibility_of_element_located(element_locator)
            )
        except Exception as e:
            self.log.error(f'Failed to wait for element disappear: {element_id} (error: {e})')
            return False
        return True
    
    def _wait_for_element_clickable(self, by, value, timeout=10):
        try:
            return WebDriverWait(self.driver, timeout).until(
                EC.element_to_be_clickable((by, value))
            )
        except Exception as e:
            self.log.error(f'Failed to wait for element clickable: {by} {value} (error: {e})')
            return None 

    def find_element(self, element_type, element_options_dict):
        html = self.current_page_source()
        soup = BeautifulSoup(html, 'html.parser')
        return soup.find_all(element_type, element_options_dict)
    
    def get_text_from_html(self, html: str):
        soup = BeautifulSoup(html, 'html.parser')
        return soup.text
        
    def get_link_url_from_html(self, html: str):
        soup = BeautifulSoup(html, 'html.parser')
        links = soup.find_all('a')
        if len(links) == 0:
            return None

        link = links[0]
        return link.get('href')

    def get_table_from_html(self, html: str, table_id: str):
        soup = BeautifulSoup(html, 'html.parser')
        return soup.find('table', {'id': table_id})
        
    def find_element_by_id(self, value):
        return self._find_element(By.ID, value)

    def find_element_by_classname(self, value):
        return self._find_element(By.CLASS_NAME, value)

    def _find_element(self, by, value):
        try:
            return self.driver.find_element(by, value)
        except NoSuchElementException:
            self.log.error(f'NoSuchElementException: {by} {value}')
            return None

    def find_link_url_by_title(self, text):
        soup = BeautifulSoup(self.current_page_source(), 'html.parser')
        links = soup.find_all('a', title=text)
        
        if len(links) == 0:
            return None

        link = links[0]
        if link:
            return link.get('href')
        else:
            return None

    def find_link_urls_by_target_rel(self, target, rel):
        soup = BeautifulSoup(self.current_page_source(), 'html.parser')
        return soup.find_all('a', target=target, rel=rel)

    def download_file(self, url, save_path: Path):
        # Apply URL prefix
        url = apply_url_prefix(url, self.settings)
        
        try:
            response = requests.get(url, stream=True, timeout=self.request_timeout)
            if response.status_code == 200:
                with open(save_path, 'wb') as file:
                    for chunk in response.iter_content(chunk_size=8192):
                        if not chunk:
                            continue
                        file.write(chunk)
                    self.log.info(f'File successfully downloaded and saved to {save_path}')
            else:
                self.log.error(f'Failed to fetch content from url {url} (status code: {response.status_code})')
        except Exception as e:
            self.log.error(f'An error occurred while fetching content from url {url}: {str(e)}')

    def click_element_by_classname(self, value, wait_timeout=30, max_attempts=3, sleep_sec=5):
        return self._click_element(By.CLASS_NAME, value, wait_timeout, max_attempts, sleep_sec)

    def click_element_by_id(self, value, wait_timeout=30, max_attempts=3, sleep_sec=5):
        return self._click_element(By.ID, value, wait_timeout, max_attempts, sleep_sec)

    def _click_element(self, by, value, wait_timeout=30, max_attempts=1, sleep_sec=5):
        if self.driver is None:
            self.open()

        for attempt in range(max_attempts):
            try:
                if self._wait_for_element_located(by, value, wait_timeout) is True:
                    break
            except Exception as e:
                self.log.warning(f'Element [{value}] not located yet, retrying... (Attempt {attempt + 1}, sleeping {sleep_sec} sec ..)')
                sleep(sleep_sec)
                sleep_sec *= 1.5

        element = self.driver.find_element(by, value)
        self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
        self.driver.execute_script("arguments[0].click();", element)
