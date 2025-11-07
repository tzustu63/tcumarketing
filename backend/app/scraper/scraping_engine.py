"""
Scraping Engine for web crawling and data extraction.
Supports both Selenium and Playwright for browser automation.
"""
import logging
import time
from typing import Optional, Dict, Any
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException

from .anti_detection import AntiDetectionManager
from app.utils.rate_limiter import get_rate_limit_manager

logger = logging.getLogger(__name__)


# Import ContactPageFinder lazily to avoid circular imports
def _get_contact_page_finder():
    from .contact_page_finder import ContactPageFinder
    return ContactPageFinder


class PageContent:
    """Represents the content of a scraped page."""
    
    def __init__(self, url: str, html: str, title: str = "", status_code: int = 200):
        self.url = url
        self.html = html
        self.title = title
        self.status_code = status_code
        self.timestamp = time.time()


class ScrapingEngine:
    """
    Web scraping engine using Selenium for browser automation.
    Handles page fetching, navigation, and resource management.
    """
    
    def __init__(
        self,
        headless: bool = True,
        timeout: int = 60,  # Increased timeout for slower connections
        use_anti_detection: bool = True,
        use_rate_limiting: bool = True,
        min_delay: float = 2.0,
        max_delay: float = 5.0
    ):
        """
        Initialize the scraping engine with a browser driver.
        
        Args:
            headless: Whether to run browser in headless mode
            timeout: Default timeout for page loads in seconds
            use_anti_detection: Whether to use anti-detection measures
            use_rate_limiting: Whether to use rate limiting
            min_delay: Minimum delay between requests
            max_delay: Maximum delay between requests
        """
        self.headless = headless
        self.timeout = timeout
        self.use_anti_detection = use_anti_detection
        self.use_rate_limiting = use_rate_limiting
        self.driver: Optional[webdriver.Chrome] = None
        
        # Initialize anti-detection manager
        if use_anti_detection:
            self.anti_detection = AntiDetectionManager(
                min_delay=min_delay,
                max_delay=max_delay
            )
        else:
            self.anti_detection = None
        
        # Initialize rate limiter
        if use_rate_limiting:
            self.rate_limiter = get_rate_limit_manager()
        else:
            self.rate_limiter = None
        
        self._initialize_driver()
        logger.info(
            f"ScrapingEngine initialized (headless={headless}, "
            f"anti_detection={use_anti_detection}, rate_limiting={use_rate_limiting})"
        )
    
    def _initialize_driver(self):
        """Initialize Selenium Chrome WebDriver with appropriate options."""
        try:
            chrome_options = ChromeOptions()
            
            if self.headless:
                chrome_options.add_argument('--headless=new')
            
            # Basic options for stability
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            
            # Anti-detection options
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            # Set language
            chrome_options.add_argument('--lang=id-ID')
            chrome_options.add_experimental_option('prefs', {
                'intl.accept_languages': 'id-ID,id,en-US,en'
            })
            
            # Set user agent
            if self.anti_detection:
                user_agent = self.anti_detection.get_user_agent()
            else:
                user_agent = (
                    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
                    'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                )
            chrome_options.add_argument(f'user-agent={user_agent}')
            
            # Set binary location for Chromium
            chrome_options.binary_location = '/usr/bin/chromium'
            
            # Use chromium-driver
            service = Service(executable_path='/usr/bin/chromedriver')
            
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.set_page_load_timeout(self.timeout)
            
            # Remove webdriver property
            self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
                'source': '''
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined
                    });
                '''
            })
            
            logger.info("Chrome WebDriver initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize WebDriver: {e}")
            raise
    
    def fetch_page(self, url: str, wait_for_element: Optional[str] = None) -> PageContent:
        """
        Fetch a single web page and return its content.
        
        Args:
            url: The URL to fetch
            wait_for_element: Optional CSS selector to wait for before returning
            
        Returns:
            PageContent object containing the page data
            
        Raises:
            WebDriverException: If page fetch fails
        """
        if not self.driver:
            raise RuntimeError("WebDriver not initialized")
        
        # Apply rate limiting
        if self.rate_limiter:
            if not self.rate_limiter.wait_and_acquire(url):
                raise RuntimeError(f"Rate limit exceeded for {url}")
        
        try:
            # Apply anti-detection delays
            if self.anti_detection:
                self.anti_detection.wait_before_request()
            
            logger.info(f"Fetching page: {url}")
            self.driver.get(url)
            
            # Wait for specific element if requested
            if wait_for_element:
                WebDriverWait(self.driver, self.timeout).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, wait_for_element))
                )
            else:
                # Default wait for body to be present
                WebDriverWait(self.driver, self.timeout).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
            
            # Get page content
            html = self.driver.page_source
            title = self.driver.title
            current_url = self.driver.current_url
            
            logger.info(f"Successfully fetched: {title}")
            return PageContent(url=current_url, html=html, title=title)
            
        except TimeoutException:
            logger.error(f"Timeout while fetching {url}")
            raise
        except WebDriverException as e:
            logger.error(f"WebDriver error while fetching {url}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error while fetching {url}: {e}")
            raise
        finally:
            # Always release rate limit
            if self.rate_limiter:
                self.rate_limiter.release()
    
    def fetch_page_with_retry(
        self,
        url: str,
        wait_for_element: Optional[str] = None,
        max_retries: int = 3
    ) -> PageContent:
        """
        Fetch a page with automatic retry on failure using exponential backoff.
        
        Args:
            url: The URL to fetch
            wait_for_element: Optional CSS selector to wait for
            max_retries: Maximum number of retry attempts
            
        Returns:
            PageContent object containing the page data
            
        Raises:
            WebDriverException: If all retry attempts fail
        """
        if self.anti_detection:
            return self.anti_detection.execute_with_retry(
                self.fetch_page,
                url,
                wait_for_element=wait_for_element,
                exceptions=(TimeoutException, WebDriverException)
            )
        else:
            # Fallback to direct fetch if anti-detection is disabled
            return self.fetch_page(url, wait_for_element)
    
    def get_google_domain(self, country_code: str) -> str:
        """
        Get the appropriate Google domain for a given country code.
        
        Args:
            country_code: Two-letter country code (e.g., 'ID', 'MY', 'SG')
            
        Returns:
            Google domain for the specified country
        """
        # Mapping of country codes to Google domains
        google_domains = {
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
            'MO': 'google.com',        # Macau (uses google.com)
        }
        
        # Return the domain for the country code, default to google.com
        domain = google_domains.get(country_code.upper(), 'google.com')
        logger.info(f"Using Google domain for {country_code}: {domain}")
        return domain
    
    def find_contact_page(self, base_url: str) -> Optional[str]:
        """
        Find the contact page URL for a given website.
        
        Args:
            base_url: Base URL of the website
            
        Returns:
            URL of the contact page if found, None otherwise
        """
        ContactPageFinder = _get_contact_page_finder()
        finder = ContactPageFinder(self)
        return finder.find_contact_page(base_url)
    
    def close(self):
        """Close the browser and clean up resources."""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("WebDriver closed successfully")
            except Exception as e:
                logger.error(f"Error closing WebDriver: {e}")
            finally:
                self.driver = None
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - ensures cleanup."""
        self.close()
    
    def __del__(self):
        """Destructor - ensures cleanup."""
        self.close()
