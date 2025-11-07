"""
Facebook Page Scraper
Extracts contact information from Facebook business pages.
"""
import logging
import time
from typing import Optional, Dict, Any
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from .scraping_engine import ScrapingEngine, PageContent

logger = logging.getLogger(__name__)


class FacebookScraper:
    """
    Scraper for extracting contact information from Facebook pages.
    Focuses on publicly accessible information without authentication.
    """
    
    # Common Facebook page URL patterns
    FACEBOOK_DOMAINS = ['facebook.com', 'fb.com', 'm.facebook.com']
    
    # Selectors for Facebook page elements
    ABOUT_SELECTORS = [
        'a[href*="/about"]',
        'a[aria-label*="About"]',
        'a[href*="about_profile_transparency"]',
    ]
    
    CONTACT_SELECTORS = [
        # Email selectors
        'a[href^="mailto:"]',
        '[data-testid*="email"]',
        'div:contains("Email")',
        
        # Phone/WhatsApp selectors
        'a[href^="tel:"]',
        'a[href*="wa.me"]',
        'a[href*="whatsapp"]',
        '[data-testid*="phone"]',
        'div:contains("Phone")',
        'div:contains("WhatsApp")',
    ]
    
    def __init__(self, scraping_engine: ScrapingEngine):
        """
        Initialize Facebook scraper.
        
        Args:
            scraping_engine: ScrapingEngine instance for browser automation
        """
        self.engine = scraping_engine
        self.driver = scraping_engine.driver
    
    def is_facebook_url(self, url: str) -> bool:
        """
        Check if URL is a Facebook page.
        
        Args:
            url: URL to check
            
        Returns:
            True if Facebook URL, False otherwise
        """
        return any(domain in url.lower() for domain in self.FACEBOOK_DOMAINS)
    
    def extract_page_info(self, url: str) -> Dict[str, Any]:
        """
        Extract contact information from a Facebook page.
        
        Args:
            url: Facebook page URL
            
        Returns:
            Dictionary containing extracted information
        """
        if not self.is_facebook_url(url):
            logger.warning(f"URL is not a Facebook page: {url}")
            return self._empty_result(url, "not_facebook_url")
        
        try:
            logger.info(f"Extracting Facebook page info: {url}")
            
            # Fetch the page
            page_content = self.engine.fetch_page_with_retry(url)
            
            # Extract page name
            page_name = self._extract_page_name()
            
            # Try to navigate to About section
            about_url = self._find_about_section(url)
            if about_url:
                logger.info(f"Found About section: {about_url}")
                self.engine.fetch_page(about_url)
                time.sleep(2)  # Wait for content to load
            
            # Extract contact information
            contact_info = self._extract_contact_info()
            
            # Extract bio/description
            description = self._extract_description()
            
            result = {
                'url': url,
                'platform': 'facebook',
                'page_name': page_name,
                'description': description,
                'emails': contact_info.get('emails', []),
                'whatsapp_numbers': contact_info.get('whatsapp', []),
                'phone_numbers': contact_info.get('phones', []),
                'raw_text': contact_info.get('raw_text', ''),
                'status': 'success',
                'error': None
            }
            
            logger.info(f"Successfully extracted Facebook page info: {page_name}")
            return result
            
        except TimeoutException:
            logger.error(f"Timeout while accessing Facebook page: {url}")
            return self._empty_result(url, "timeout")
        
        except Exception as e:
            logger.error(f"Error extracting Facebook page info: {e}")
            return self._empty_result(url, f"error: {str(e)}")
    
    def _extract_page_name(self) -> str:
        """Extract the Facebook page name."""
        try:
            # Try multiple selectors for page name
            selectors = [
                'h1',
                '[role="heading"]',
                'title',
            ]
            
            for selector in selectors:
                try:
                    element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    name = element.text.strip()
                    if name and len(name) > 0:
                        return name
                except NoSuchElementException:
                    continue
            
            # Fallback to page title
            return self.driver.title.replace(' | Facebook', '').strip()
            
        except Exception as e:
            logger.warning(f"Could not extract page name: {e}")
            return "Unknown"
    
    def _find_about_section(self, base_url: str) -> Optional[str]:
        """
        Find the About section URL.
        
        Args:
            base_url: Base Facebook page URL
            
        Returns:
            About section URL if found, None otherwise
        """
        try:
            # Try to find About link
            for selector in self.ABOUT_SELECTORS:
                try:
                    element = WebDriverWait(self.driver, 5).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    about_url = element.get_attribute('href')
                    if about_url:
                        return about_url
                except TimeoutException:
                    continue
            
            # Construct About URL manually
            if '/profile.php?id=' in base_url:
                # Profile ID format
                return base_url + '&sk=about'
            else:
                # Username format
                clean_url = base_url.rstrip('/')
                return clean_url + '/about'
                
        except Exception as e:
            logger.warning(f"Could not find About section: {e}")
            return None
    
    def _extract_contact_info(self) -> Dict[str, Any]:
        """
        Extract contact information from the current page.
        
        Returns:
            Dictionary with emails, phones, and WhatsApp numbers
        """
        result = {
            'emails': [],
            'whatsapp': [],
            'phones': [],
            'raw_text': ''
        }
        
        try:
            # Get page source for text extraction
            page_text = self.driver.find_element(By.TAG_NAME, 'body').text
            result['raw_text'] = page_text[:1000]  # Store first 1000 chars
            
            # Extract emails from mailto links
            try:
                email_links = self.driver.find_elements(By.CSS_SELECTOR, 'a[href^="mailto:"]')
                for link in email_links:
                    href = link.get_attribute('href')
                    if href:
                        email = href.replace('mailto:', '').split('?')[0].strip()
                        if email and email not in result['emails']:
                            result['emails'].append(email)
            except Exception as e:
                logger.debug(f"Error extracting emails from links: {e}")
            
            # Extract phone numbers from tel links
            try:
                phone_links = self.driver.find_elements(By.CSS_SELECTOR, 'a[href^="tel:"]')
                for link in phone_links:
                    href = link.get_attribute('href')
                    if href:
                        phone = href.replace('tel:', '').strip()
                        if phone:
                            # Check if it's a WhatsApp number (Indonesian format)
                            if phone.startswith('+62') or phone.startswith('62') or phone.startswith('08'):
                                if phone not in result['whatsapp']:
                                    result['whatsapp'].append(phone)
                            else:
                                if phone not in result['phones']:
                                    result['phones'].append(phone)
            except Exception as e:
                logger.debug(f"Error extracting phones from links: {e}")
            
            # Extract WhatsApp from wa.me links
            try:
                wa_links = self.driver.find_elements(By.CSS_SELECTOR, 'a[href*="wa.me"], a[href*="whatsapp"]')
                for link in wa_links:
                    href = link.get_attribute('href')
                    if href and 'wa.me' in href:
                        # Extract number from wa.me/62xxx format
                        import re
                        match = re.search(r'wa\.me/(\+?[\d]+)', href)
                        if match:
                            number = match.group(1)
                            if number not in result['whatsapp']:
                                result['whatsapp'].append(number)
            except Exception as e:
                logger.debug(f"Error extracting WhatsApp from links: {e}")
            
            # Use ContactExtractor for additional pattern matching
            from ..extractor.contact_extractor import ContactExtractor
            extractor = ContactExtractor()
            extracted = extractor.extract_from_text(page_text)
            
            # Merge results
            for email in extracted.emails:
                if email not in result['emails']:
                    result['emails'].append(email)
            
            for wa in extracted.whatsapp_numbers:
                if wa not in result['whatsapp']:
                    result['whatsapp'].append(wa)
            
        except Exception as e:
            logger.error(f"Error extracting contact info: {e}")
        
        return result
    
    def _extract_description(self) -> str:
        """Extract page description/bio."""
        try:
            # Try to find description in various locations
            selectors = [
                '[data-testid="page_description"]',
                'div[class*="bio"]',
                'div[class*="description"]',
            ]
            
            for selector in selectors:
                try:
                    element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    desc = element.text.strip()
                    if desc:
                        return desc
                except NoSuchElementException:
                    continue
            
            return ""
            
        except Exception as e:
            logger.debug(f"Could not extract description: {e}")
            return ""
    
    def _empty_result(self, url: str, error: str) -> Dict[str, Any]:
        """
        Create an empty result with error information.
        
        Args:
            url: The URL that was attempted
            error: Error message
            
        Returns:
            Empty result dictionary
        """
        return {
            'url': url,
            'platform': 'facebook',
            'page_name': None,
            'description': None,
            'emails': [],
            'whatsapp_numbers': [],
            'phone_numbers': [],
            'raw_text': '',
            'status': 'failed',
            'error': error
        }
