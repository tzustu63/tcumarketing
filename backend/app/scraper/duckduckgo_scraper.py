"""
DuckDuckGo Search scraper for extracting search results.
DuckDuckGo has weaker anti-bot detection compared to Google.
"""
import logging
import time
import urllib.parse
from typing import List, Optional
from dataclasses import dataclass
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from .scraping_engine import ScrapingEngine

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """Represents a single search result."""
    url: str
    title: str
    description: str
    position: int
    platform: str = "website"  # website, facebook, instagram


class DuckDuckGoScraper:
    """
    DuckDuckGo Search scraper that extracts search results.
    """
    
    def __init__(self, engine: ScrapingEngine):
        """
        Initialize DuckDuckGo scraper with a scraping engine.
        
        Args:
            engine: ScrapingEngine instance to use for scraping
        """
        self.engine = engine
        self.base_url = "https://duckduckgo.com/"
    
    def search_duckduckgo(
        self,
        query: str,
        max_results: int = 10
    ) -> List[SearchResult]:
        """
        Execute a DuckDuckGo search and extract results.
        
        Args:
            query: Search query string
            max_results: Maximum number of results to return
            
        Returns:
            List of SearchResult objects
        """
        all_results = []
        
        try:
            # Build search URL
            params = {'q': query}
            url = f"{self.base_url}?{urllib.parse.urlencode(params)}"
            
            logger.info(f"Searching DuckDuckGo for: {query} (max_results: {max_results})")
            
            # Fetch the page
            page_content = self.engine.fetch_page(url)
            
            # Wait a bit for results to load
            time.sleep(2)
            
            # Parse initial results
            results = self._parse_search_results()
            all_results.extend(results)
            
            # If we need more results and haven't reached max_results, try scrolling
            scroll_attempts = 0
            max_scroll_attempts = min(10, (max_results // 10) + 1)  # Limit scrolling attempts
            
            while len(all_results) < max_results and scroll_attempts < max_scroll_attempts:
                scroll_attempts += 1
                logger.info(f"Scrolling for more results (attempt {scroll_attempts}/{max_scroll_attempts})")
                
                # Scroll to bottom to trigger lazy loading
                try:
                    self.engine.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(2)  # Wait for new results to load
                    
                    # Parse new results
                    new_results = self._parse_search_results()
                    
                    # Check if we got new results
                    if len(new_results) <= len(all_results):
                        logger.info("No new results found after scrolling, stopping")
                        break
                    
                    # Add only new results
                    all_results = new_results
                    logger.info(f"Total results after scroll: {len(all_results)}")
                    
                except Exception as e:
                    logger.warning(f"Error during scrolling: {e}")
                    break
            
            # Limit to max_results
            all_results = all_results[:max_results]
            
            logger.info(f"Total results scraped from DuckDuckGo: {len(all_results)}/{max_results}")
            
        except Exception as e:
            logger.error(f"Error scraping DuckDuckGo: {e}", exc_info=True)
        
        return all_results
    
    def _parse_search_results(self) -> List[SearchResult]:
        """
        Parse DuckDuckGo search results from the page.
        
        Returns:
            List of SearchResult objects
        """
        results = []
        
        try:
            # DuckDuckGo uses article tags or specific result containers
            selectors = [
                'article[data-testid="result"]',
                'li[data-layout="organic"]',
                'div.result',
                'div[data-testid="result"]'
            ]
            
            result_elements = []
            for selector in selectors:
                try:
                    elements = self.engine.driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        logger.info(f"Found {len(elements)} results with selector: {selector}")
                        result_elements = elements
                        break
                except Exception as e:
                    logger.debug(f"Selector {selector} failed: {e}")
                    continue
            
            if not result_elements:
                logger.warning("No search result elements found with any selector")
                return results
            
            for idx, element in enumerate(result_elements):
                try:
                    result = self._extract_result_data(element, idx + 1)
                    if result:
                        results.append(result)
                except Exception as e:
                    logger.debug(f"Failed to extract result {idx}: {e}")
                    continue
            
        except Exception as e:
            logger.error(f"Error parsing search results: {e}")
        
        return results
    
    def _extract_result_data(self, element, position: int) -> Optional[SearchResult]:
        """
        Extract data from a single search result element.
        
        Args:
            element: Selenium WebElement representing a search result
            position: Position of this result in the overall list
            
        Returns:
            SearchResult object or None if extraction fails
        """
        try:
            # Extract URL
            url = None
            link_selectors = [
                'a[data-testid="result-title-a"]',
                'a.result__a',
                'h2 a',
                'a[href]'
            ]
            
            for selector in link_selectors:
                try:
                    link_element = element.find_element(By.CSS_SELECTOR, selector)
                    url = link_element.get_attribute('href')
                    if url and not url.startswith('javascript:'):
                        break
                except NoSuchElementException:
                    continue
            
            if not url:
                return None
            
            # Extract title
            title = ""
            title_selectors = [
                'h2[data-testid="result-title"]',
                'h2.result__title',
                'h2',
                'a[data-testid="result-title-a"]'
            ]
            
            for selector in title_selectors:
                try:
                    title_element = element.find_element(By.CSS_SELECTOR, selector)
                    title = title_element.text.strip()
                    if title:
                        break
                except NoSuchElementException:
                    continue
            
            if not title:
                title = url
            
            # Extract description
            description = ""
            desc_selectors = [
                'div[data-testid="result-snippet"]',
                'div.result__snippet',
                'div[data-result="snippet"]'
            ]
            
            for selector in desc_selectors:
                try:
                    desc_element = element.find_element(By.CSS_SELECTOR, selector)
                    description = desc_element.text.strip()
                    if description:
                        break
                except NoSuchElementException:
                    continue
            
            # Determine platform based on URL
            platform = self._identify_platform(url)
            
            return SearchResult(
                url=url,
                title=title,
                description=description,
                position=position,
                platform=platform
            )
            
        except Exception as e:
            logger.debug(f"Error extracting result data: {e}")
            return None
    
    def _identify_platform(self, url: str) -> str:
        """
        Identify the platform type based on URL.
        
        Args:
            url: The URL to analyze
            
        Returns:
            Platform identifier: 'facebook', 'instagram', or 'website'
        """
        url_lower = url.lower()
        
        if 'facebook.com' in url_lower or 'fb.com' in url_lower:
            return 'facebook'
        elif 'instagram.com' in url_lower:
            return 'instagram'
        else:
            return 'website'
