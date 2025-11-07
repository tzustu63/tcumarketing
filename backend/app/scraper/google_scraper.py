"""
Google Search scraper for extracting search results.
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
    """Represents a single Google search result."""
    url: str
    title: str
    description: str
    position: int
    platform: str = "website"  # website, facebook, instagram


class GoogleScraper:
    """
    Google Search scraper that extracts search results including URLs, titles, and descriptions.
    Supports multi-page navigation.
    """
    
    # Country-specific Google domains
    GOOGLE_DOMAINS = {
        'ID': 'google.co.id',      # Indonesia
        'MY': 'google.com.my',     # Malaysia
        'SG': 'google.com.sg',     # Singapore
        'TH': 'google.co.th',      # Thailand
        'VN': 'google.com.vn',     # Vietnam
        'PH': 'google.com.ph',     # Philippines
        'MM': 'google.com.mm',     # Myanmar
        'KH': 'google.com.kh',     # Cambodia
        'IN': 'google.co.in',      # India
        'HK': 'google.com.hk',     # Hong Kong
        'MO': 'google.com.mo',     # Macau
        'US': 'google.com',        # United States (default)
    }
    
    def __init__(self, engine: ScrapingEngine, country_code: str = 'ID'):
        """
        Initialize Google scraper with a scraping engine.
        
        Args:
            engine: ScrapingEngine instance to use for scraping
            country_code: Two-letter country code (e.g., 'ID' for Indonesia)
        """
        self.engine = engine
        self.country_code = country_code
        domain = self.GOOGLE_DOMAINS.get(country_code, 'google.com')
        self.base_url = f"https://www.{domain}/search"
        logger.info(f"GoogleScraper initialized for country {country_code} using {domain}")
    
    def search_google(
        self,
        query: str,
        max_pages: int = 5,
        results_per_page: int = 10
    ) -> List[SearchResult]:
        """
        Execute a Google search and extract results from multiple pages.
        
        Args:
            query: Search query string
            max_pages: Maximum number of result pages to scrape
            results_per_page: Expected results per page (for pagination)
            
        Returns:
            List of SearchResult objects
        """
        all_results = []
        
        for page in range(max_pages):
            try:
                start = page * results_per_page
                results = self._scrape_page(query, start)
                
                if not results:
                    logger.info(f"No more results found at page {page + 1}")
                    break
                
                all_results.extend(results)
                logger.info(f"Scraped page {page + 1}: {len(results)} results")
                
                # Check if there's a next page
                if not self._has_next_page():
                    logger.info("No more pages available")
                    break
                
                # Delay between pages (will be enhanced by anti-detection)
                time.sleep(2)
                
            except Exception as e:
                logger.error(f"Error scraping page {page + 1}: {e}")
                break
        
        logger.info(f"Total results scraped: {len(all_results)}")
        return all_results
    
    def _scrape_page(self, query: str, start: int = 0) -> List[SearchResult]:
        """
        Scrape a single page of Google search results.
        
        Args:
            query: Search query
            start: Starting position for pagination
            
        Returns:
            List of SearchResult objects from this page
        """
        # Build search URL
        params = {
            'q': query,
            'start': start,
            'num': 10
        }
        url = f"{self.base_url}?{urllib.parse.urlencode(params)}"
        
        # Fetch the page
        page_content = self.engine.fetch_page(url)
        
        # Parse results
        results = self._parse_search_results(page_content.html, start)
        return results
    
    def _parse_search_results(self, html: str, start_position: int = 0) -> List[SearchResult]:
        """
        Parse Google search results from HTML.
        
        Args:
            html: HTML content of the search results page
            start_position: Starting position for result numbering
            
        Returns:
            List of SearchResult objects
        """
        results = []
        
        try:
            # Find all search result containers
            # Try multiple selectors as Google's HTML structure varies
            selectors = [
                'div.g',  # Traditional selector
                'div[data-sokoban-container]',  # Newer structure
                'div.Gx5Zad',  # Alternative structure
                'div[jscontroller]',  # Generic container
            ]
            
            result_elements = []
            for selector in selectors:
                elements = self.engine.driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    logger.info(f"Found {len(elements)} elements with selector: {selector}")
                    result_elements = elements
                    break
            
            if not result_elements:
                logger.warning("No search result elements found with any selector")
                # Log page source for debugging
                logger.warning(f"Page title: {self.engine.driver.title}")
                logger.warning(f"Current URL: {self.engine.driver.current_url}")
                
                # Try to save screenshot for debugging
                try:
                    screenshot_path = f"/app/logs/google_search_debug_{int(time.time())}.png"
                    self.engine.driver.save_screenshot(screenshot_path)
                    logger.warning(f"Screenshot saved to: {screenshot_path}")
                except Exception as e:
                    logger.warning(f"Could not save screenshot: {e}")
                
                # Log first 500 chars of page source
                page_source = self.engine.driver.page_source[:500]
                logger.warning(f"Page source preview: {page_source}")
                
                return results
            
            for idx, element in enumerate(result_elements):
                try:
                    result = self._extract_result_data(element, start_position + idx + 1)
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
            # Extract URL - try multiple approaches
            url = None
            link_selectors = ['a', 'a[href]', 'a[jsname]']
            for selector in link_selectors:
                try:
                    link_element = element.find_element(By.CSS_SELECTOR, selector)
                    url = link_element.get_attribute('href')
                    
                    # Filter out invalid URLs
                    if url and self._is_valid_result_url(url):
                        break
                    else:
                        url = None
                except NoSuchElementException:
                    continue
            
            if not url:
                return None
            
            # Extract title - try multiple selectors
            title = ""
            title_selectors = ['h3', 'h3.LC20lb', 'div[role="heading"]', 'h3[class]']
            for selector in title_selectors:
                try:
                    title_element = element.find_element(By.CSS_SELECTOR, selector)
                    title = title_element.text.strip()
                    if title:
                        break
                except NoSuchElementException:
                    continue
            
            if not title:
                # Use URL as fallback title
                title = url
            
            # Extract description (snippet)
            description = ""
            try:
                # Try multiple selectors for description
                desc_selectors = [
                    'div[data-sncf="1"]',
                    'div.VwiC3b',
                    'span.aCOpRe',
                    'div.s'
                ]
                
                for selector in desc_selectors:
                    try:
                        desc_element = element.find_element(By.CSS_SELECTOR, selector)
                        description = desc_element.text.strip()
                        if description:
                            break
                    except NoSuchElementException:
                        continue
                        
            except Exception as e:
                logger.debug(f"Could not extract description: {e}")
            
            # Determine platform based on URL
            platform = self._identify_platform(url)
            
            return SearchResult(
                url=url,
                title=title,
                description=description,
                position=position,
                platform=platform
            )
            
        except NoSuchElementException as e:
            logger.debug(f"Missing element in result: {e}")
            return None
        except Exception as e:
            logger.error(f"Error extracting result data: {e}")
            return None
    
    def _is_valid_result_url(self, url: str) -> bool:
        """
        Check if URL is a valid search result (not Google's own pages).
        
        Args:
            url: URL to validate
            
        Returns:
            True if valid result URL, False otherwise
        """
        if not url or not url.startswith('http'):
            return False
        
        # Filter out invalid patterns
        invalid_patterns = [
            'javascript:',
            '/search?',
            '/url?',
            'google.com/search',
            'google.com/webhp',
            'google.com/preferences',
            'google.com/advanced_search',
            'google.com/intl',
            'support.google.com',
            'accounts.google.com',
            'policies.google.com',
            'maps.google.com',
            'translate.google.com',
        ]
        
        url_lower = url.lower()
        for pattern in invalid_patterns:
            if pattern in url_lower:
                return False
        
        return True
    
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
    
    def _has_next_page(self) -> bool:
        """
        Check if there is a next page of results available.
        
        Returns:
            True if next page exists, False otherwise
        """
        try:
            # Look for "Next" button or next page link
            next_selectors = [
                'a#pnnext',
                'a[aria-label="Next page"]',
                'td.b a[aria-label*="Next"]'
            ]
            
            for selector in next_selectors:
                try:
                    next_button = self.engine.driver.find_element(By.CSS_SELECTOR, selector)
                    if next_button and next_button.is_displayed():
                        return True
                except NoSuchElementException:
                    continue
            
            return False
            
        except Exception as e:
            logger.debug(f"Error checking for next page: {e}")
            return False
