"""
Contact page finder for locating contact information pages on websites.
"""
import logging
from typing import List, Optional, Set
from urllib.parse import urljoin, urlparse
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, TimeoutException

from .scraping_engine import ScrapingEngine

logger = logging.getLogger(__name__)


class ContactPageFinder:
    """
    Finds contact pages on websites by checking common paths and link text.
    """
    
    # Common contact page paths (Indonesian and English)
    COMMON_PATHS = [
        '/kontak',
        '/kontak-kami',
        '/hubungi-kami',
        '/hubungi',
        '/contact',
        '/contact-us',
        '/contactus',
        '/about/contact',
        '/tentang/kontak',
        '/info/kontak',
        '/info/contact',
        '/about-us',
        '/tentang-kami',
        '/about',
        '/tentang',
    ]
    
    # Common link text patterns for contact pages (case-insensitive)
    CONTACT_LINK_PATTERNS = [
        'kontak kami',
        'kontak',
        'hubungi kami',
        'hubungi',
        'contact us',
        'contact',
        'get in touch',
        'reach us',
        'tentang kami',
        'about us',
        'about',
    ]
    
    def __init__(self, engine: ScrapingEngine):
        """
        Initialize contact page finder.
        
        Args:
            engine: ScrapingEngine instance to use for navigation
        """
        self.engine = engine
    
    def find_contact_page(self, base_url: str) -> Optional[str]:
        """
        Find the contact page URL for a given website.
        
        Tries multiple strategies:
        1. Check common contact page paths
        2. Search for contact links in the navigation
        3. Search for contact links in the footer
        
        Args:
            base_url: Base URL of the website
            
        Returns:
            URL of the contact page if found, None otherwise
        """
        logger.info(f"Searching for contact page on: {base_url}")
        
        # Normalize base URL
        parsed = urlparse(base_url)
        base_url = f"{parsed.scheme}://{parsed.netloc}"
        
        # Strategy 1: Try common paths
        contact_url = self._try_common_paths(base_url)
        if contact_url:
            logger.info(f"Found contact page via common path: {contact_url}")
            return contact_url
        
        # Strategy 2: Search for contact links on the homepage
        try:
            self.engine.fetch_page(base_url)
            contact_url = self._find_contact_link()
            if contact_url:
                logger.info(f"Found contact page via link search: {contact_url}")
                return contact_url
        except Exception as e:
            logger.error(f"Error searching for contact links: {e}")
        
        logger.warning(f"Could not find contact page for: {base_url}")
        return None
    
    def _try_common_paths(self, base_url: str) -> Optional[str]:
        """
        Try common contact page paths.
        
        Args:
            base_url: Base URL of the website
            
        Returns:
            URL if a valid contact page is found, None otherwise
        """
        for path in self.COMMON_PATHS:
            url = urljoin(base_url, path)
            
            try:
                # Try to fetch the page
                page_content = self.engine.fetch_page(url)
                
                # Check if it's a valid page (not 404)
                if self._is_valid_contact_page(page_content.html):
                    return url
                    
            except TimeoutException:
                logger.debug(f"Timeout accessing {url}")
                continue
            except Exception as e:
                logger.debug(f"Error accessing {url}: {e}")
                continue
        
        return None
    
    def _find_contact_link(self) -> Optional[str]:
        """
        Find contact page link in the current page.
        
        Searches navigation menus and footer for contact links.
        
        Returns:
            URL of contact page if found, None otherwise
        """
        if not self.engine.driver:
            return None
        
        try:
            # Get all links on the page
            links = self.engine.driver.find_elements(By.TAG_NAME, 'a')
            
            # Check each link
            for link in links:
                try:
                    href = link.get_attribute('href')
                    text = link.text.strip().lower()
                    
                    if not href:
                        continue
                    
                    # Check if link text matches contact patterns
                    if self._is_contact_link(text, href):
                        return href
                        
                except Exception as e:
                    logger.debug(f"Error processing link: {e}")
                    continue
            
        except Exception as e:
            logger.error(f"Error finding contact links: {e}")
        
        return None
    
    def _is_contact_link(self, text: str, href: str) -> bool:
        """
        Check if a link is likely a contact page link.
        
        Args:
            text: Link text (lowercase)
            href: Link URL
            
        Returns:
            True if likely a contact link, False otherwise
        """
        # Check text patterns
        for pattern in self.CONTACT_LINK_PATTERNS:
            if pattern in text:
                return True
        
        # Check URL patterns
        href_lower = href.lower()
        contact_keywords = ['kontak', 'hubungi', 'contact', 'about', 'tentang']
        
        for keyword in contact_keywords:
            if keyword in href_lower:
                return True
        
        return False
    
    def _is_valid_contact_page(self, html: str) -> bool:
        """
        Check if the HTML content appears to be a valid contact page.
        
        Args:
            html: HTML content to check
            
        Returns:
            True if appears to be a contact page, False otherwise
        """
        html_lower = html.lower()
        
        # Check for 404 indicators
        error_indicators = ['404', 'not found', 'page not found', 'tidak ditemukan']
        for indicator in error_indicators:
            if indicator in html_lower:
                return False
        
        # Check for contact-related content
        contact_indicators = [
            'email',
            'phone',
            'telepon',
            'whatsapp',
            'address',
            'alamat',
            '@',
            '+62',
        ]
        
        indicator_count = sum(1 for indicator in contact_indicators if indicator in html_lower)
        
        # If we find at least 2 contact indicators, consider it valid
        return indicator_count >= 2
    
    def get_all_contact_candidates(self, base_url: str) -> List[str]:
        """
        Get all potential contact page URLs without validation.
        
        Useful for batch processing or when you want to check multiple pages.
        
        Args:
            base_url: Base URL of the website
            
        Returns:
            List of potential contact page URLs
        """
        candidates = []
        
        # Add common paths
        parsed = urlparse(base_url)
        base = f"{parsed.scheme}://{parsed.netloc}"
        
        for path in self.COMMON_PATHS:
            candidates.append(urljoin(base, path))
        
        # Try to find links on homepage
        try:
            self.engine.fetch_page(base_url)
            
            if self.engine.driver:
                links = self.engine.driver.find_elements(By.TAG_NAME, 'a')
                
                for link in links:
                    try:
                        href = link.get_attribute('href')
                        text = link.text.strip().lower()
                        
                        if href and self._is_contact_link(text, href):
                            if href not in candidates:
                                candidates.append(href)
                    except:
                        continue
                        
        except Exception as e:
            logger.error(f"Error getting contact candidates: {e}")
        
        return candidates
