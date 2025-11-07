"""
Instagram Page Scraper
Extracts contact information from Instagram business profiles.
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


class InstagramScraper:
    """
    Scraper for extracting contact information from Instagram profiles.
    Focuses on publicly accessible information without authentication.
    """
    
    # Common Instagram URL patterns
    INSTAGRAM_DOMAINS = ['instagram.com', 'instagr.am']
    
    # Selectors for Instagram profile elements
    BIO_SELECTORS = [
        'div._aa_c',  # Bio container
        'span._aacl',  # Bio text
        'div[class*="bio"]',
        'h1 + div',  # Usually bio is after username
    ]
    
    CONTACT_BUTTON_SELECTORS = [
        'a[href^="mailto:"]',
        'a[href^="tel:"]',
        'a[href*="wa.me"]',
        'a[href*="whatsapp"]',
        'button:contains("Contact")',
        'button:contains("Email")',
    ]
    
    def __init__(self, scraping_engine: ScrapingEngine):
        """
        Initialize Instagram scraper.
        
        Args:
            scraping_engine: ScrapingEngine instance for browser automation
        """
        self.engine = scraping_engine
        self.driver = scraping_engine.driver
    
    def is_instagram_url(self, url: str) -> bool:
        """
        Check if URL is an Instagram profile.
        
        Args:
            url: URL to check
            
        Returns:
            True if Instagram URL, False otherwise
        """
        return any(domain in url.lower() for domain in self.INSTAGRAM_DOMAINS)
    
    def extract_profile_info(self, url: str) -> Dict[str, Any]:
        """
        Extract contact information from an Instagram profile.
        
        Args:
            url: Instagram profile URL
            
        Returns:
            Dictionary containing extracted information
        """
        if not self.is_instagram_url(url):
            logger.warning(f"URL is not an Instagram profile: {url}")
            return self._empty_result(url, "not_instagram_url")
        
        try:
            logger.info(f"Extracting Instagram profile info: {url}")
            
            # Fetch the page
            page_content = self.engine.fetch_page_with_retry(url)
            
            # Wait for profile to load
            time.sleep(3)
            
            # Extract username
            username = self._extract_username(url)
            
            # Extract bio/description
            bio = self._extract_bio()
            
            # Extract contact information from bio and links
            contact_info = self._extract_contact_info(bio)
            
            # Try to find external links
            external_links = self._extract_external_links()
            
            result = {
                'url': url,
                'platform': 'instagram',
                'username': username,
                'bio': bio,
                'external_links': external_links,
                'emails': contact_info.get('emails', []),
                'whatsapp_numbers': contact_info.get('whatsapp', []),
                'phone_numbers': contact_info.get('phones', []),
                'raw_text': contact_info.get('raw_text', ''),
                'status': 'success',
                'error': None
            }
            
            logger.info(f"Successfully extracted Instagram profile info: {username}")
            return result
            
        except TimeoutException:
            logger.error(f"Timeout while accessing Instagram profile: {url}")
            return self._empty_result(url, "timeout")
        
        except Exception as e:
            logger.error(f"Error extracting Instagram profile info: {e}")
            return self._empty_result(url, f"error: {str(e)}")
    
    def _extract_username(self, url: str) -> str:
        """
        Extract username from URL or page.
        
        Args:
            url: Instagram profile URL
            
        Returns:
            Username
        """
        try:
            # Try to extract from URL first
            import re
            match = re.search(r'instagram\.com/([^/?]+)', url)
            if match:
                return match.group(1)
            
            # Try to find username in page
            try:
                username_element = self.driver.find_element(By.TAG_NAME, 'h1')
                return username_element.text.strip()
            except NoSuchElementException:
                pass
            
            # Fallback to page title
            title = self.driver.title
            if title:
                return title.split('(')[0].strip().replace('@', '')
            
            return "Unknown"
            
        except Exception as e:
            logger.warning(f"Could not extract username: {e}")
            return "Unknown"
    
    def _extract_bio(self) -> str:
        """
        Extract profile bio/description.
        
        Returns:
            Bio text
        """
        try:
            # Try multiple selectors
            for selector in self.BIO_SELECTORS:
                try:
                    element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    bio = element.text.strip()
                    if bio and len(bio) > 0:
                        return bio
                except NoSuchElementException:
                    continue
            
            # Try to find bio by looking for common patterns
            try:
                # Bio is usually in a specific section
                sections = self.driver.find_elements(By.TAG_NAME, 'section')
                for section in sections:
                    text = section.text.strip()
                    # Bio usually contains contact info or description
                    if any(keyword in text.lower() for keyword in ['email', 'wa', 'whatsapp', 'contact', 'dm']):
                        return text
            except Exception:
                pass
            
            return ""
            
        except Exception as e:
            logger.debug(f"Could not extract bio: {e}")
            return ""
    
    def _extract_contact_info(self, bio: str) -> Dict[str, Any]:
        """
        Extract contact information from bio and page.
        
        Args:
            bio: Profile bio text
            
        Returns:
            Dictionary with emails, phones, and WhatsApp numbers
        """
        result = {
            'emails': [],
            'whatsapp': [],
            'phones': [],
            'raw_text': bio
        }
        
        try:
            # Get full page text
            page_text = self.driver.find_element(By.TAG_NAME, 'body').text
            combined_text = bio + '\n' + page_text[:500]
            result['raw_text'] = combined_text
            
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
            
            # Use ContactExtractor for pattern matching in bio
            from ..extractor.contact_extractor import ContactExtractor
            extractor = ContactExtractor()
            extracted = extractor.extract_from_text(combined_text)
            
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
    
    def _extract_external_links(self) -> list:
        """
        Extract external links from profile (link-in-bio).
        
        Returns:
            List of external URLs
        """
        links = []
        
        try:
            # Look for external link elements
            link_selectors = [
                'a[href*="http"]',
                'a[target="_blank"]',
            ]
            
            for selector in link_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        href = element.get_attribute('href')
                        if href and not any(domain in href for domain in self.INSTAGRAM_DOMAINS):
                            # Filter out Instagram internal links
                            if href not in links and 'instagram.com' not in href:
                                links.append(href)
                except Exception:
                    continue
            
        except Exception as e:
            logger.debug(f"Could not extract external links: {e}")
        
        return links
    
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
            'platform': 'instagram',
            'username': None,
            'bio': None,
            'external_links': [],
            'emails': [],
            'whatsapp_numbers': [],
            'phone_numbers': [],
            'raw_text': '',
            'status': 'failed',
            'error': error
        }
