"""
HTML Parser and Contact Information Extractor
"""
import re
from typing import List, Optional, Dict, Set
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from dataclasses import dataclass

from .contact_extractor import ContactExtractor, ContactInfo


@dataclass
class PageAnalysis:
    """Page analysis result"""
    is_contact_page: bool
    confidence_score: float
    contact_indicators: List[str]
    links_found: List[str]


class HTMLParser:
    """
    Parse HTML and extract contact information
    Alias for HTMLContactParser for backward compatibility
    """
    
    # Contact page keywords (Indonesian and English)
    CONTACT_PAGE_KEYWORDS = [
        # Indonesian
        'kontak', 'hubungi', 'hubungi kami', 'kontak kami',
        'tentang kami', 'alamat', 'informasi',
        # English
        'contact', 'contact us', 'get in touch', 'reach us',
        'about us', 'about', 'address', 'location',
        # Mixed
        'contact-us', 'contactus', 'hubungi-kami'
    ]
    
    # Common contact page URL patterns
    CONTACT_URL_PATTERNS = [
        r'/kontak',
        r'/hubungi',
        r'/contact',
        r'/about',
        r'/tentang',
        r'/alamat',
        r'/informasi',
        r'/info',
        r'/contact-us',
        r'/hubungi-kami',
        r'/kontak-kami',
    ]
    
    # HTML tags that commonly contain contact info
    CONTACT_TAGS = ['p', 'div', 'span', 'a', 'li', 'td', 'footer', 'address']
    
    # Sections to prioritize
    PRIORITY_SECTIONS = ['footer', 'contact', 'address', 'aside']
    
    def __init__(self):
        """Initialize the HTML parser"""
        self.contact_extractor = ContactExtractor()
        self.contact_url_regex = re.compile('|'.join(self.CONTACT_URL_PATTERNS), re.IGNORECASE)
    
    def parse_html(self, html: str, base_url: Optional[str] = None, institution_name: Optional[str] = None) -> Dict[str, any]:
        """
        Parse HTML and extract contact information
        
        Args:
            html: HTML content
            base_url: Base URL for resolving relative links
            institution_name: Optional institution name for classification
            
        Returns:
            Dictionary with extracted information including title, text, and contact info
        """
        if not html:
            return {
                "title": "",
                "text": "",
                "emails": [],
                "whatsapp_numbers": [],
                "institution_type": None
            }
        
        # Parse HTML
        soup = BeautifulSoup(html, 'html.parser')
        
        # Extract title
        title_tag = soup.find('title')
        title = title_tag.get_text(strip=True) if title_tag else ""
        
        # Remove script and style elements
        for element in soup(['script', 'style', 'noscript']):
            element.decompose()
        
        # Extract text from priority sections first
        priority_text = self._extract_priority_sections(soup)
        
        # Extract all text
        all_text = soup.get_text(separator=' ', strip=True)
        
        # Combine priority text with all text (priority text first)
        combined_text = priority_text + " " + all_text
        
        # Extract contact information with classification
        contact_info = self.contact_extractor.extract_from_text(
            combined_text, 
            institution_name=institution_name or title
        )
        
        # Also check for mailto links and tel links
        mailto_emails = self._extract_mailto_links(soup)
        tel_numbers = self._extract_tel_links(soup)
        
        # Merge results
        all_emails = list(set(contact_info.emails + mailto_emails))
        all_whatsapp = list(set(contact_info.whatsapp_numbers + tel_numbers))
        
        return {
            "title": title,
            "text": combined_text[:1000],
            "emails": all_emails,
            "whatsapp_numbers": all_whatsapp,
            "institution_type": contact_info.institution_type
        }
    
    def identify_contact_page(self, html: str, url: Optional[str] = None) -> PageAnalysis:
        """
        Identify if a page is a contact page
        
        Args:
            html: HTML content
            url: Page URL (optional)
            
        Returns:
            PageAnalysis with identification results
        """
        if not html:
            return PageAnalysis(
                is_contact_page=False,
                confidence_score=0.0,
                contact_indicators=[],
                links_found=[]
            )
        
        soup = BeautifulSoup(html, 'html.parser')
        indicators = []
        score = 0.0
        
        # Check URL
        if url:
            if self.contact_url_regex.search(url):
                score += 30.0
                indicators.append(f"URL matches contact pattern: {url}")
        
        # Check page title
        title = soup.find('title')
        if title:
            title_text = title.get_text().lower()
            for keyword in self.CONTACT_PAGE_KEYWORDS:
                if keyword in title_text:
                    score += 20.0
                    indicators.append(f"Title contains: {keyword}")
                    break
        
        # Check headings (h1, h2, h3)
        for heading_tag in ['h1', 'h2', 'h3']:
            headings = soup.find_all(heading_tag)
            for heading in headings:
                heading_text = heading.get_text().lower()
                for keyword in self.CONTACT_PAGE_KEYWORDS:
                    if keyword in heading_text:
                        score += 15.0
                        indicators.append(f"Heading contains: {keyword}")
                        break
        
        # Check for contact forms
        forms = soup.find_all('form')
        for form in forms:
            form_text = form.get_text().lower()
            if any(keyword in form_text for keyword in ['email', 'message', 'pesan', 'nama', 'name']):
                score += 20.0
                indicators.append("Contact form found")
                break
        
        # Check for email and phone patterns in text
        text = soup.get_text()
        if '@' in text:
            score += 10.0
            indicators.append("Email pattern found")
        
        if re.search(r'(\+62|08)\s?\d{8,11}', text):
            score += 10.0
            indicators.append("Phone pattern found")
        
        # Check for address/location indicators
        address_keywords = ['alamat', 'address', 'lokasi', 'location', 'jalan', 'street']
        text_lower = text.lower()
        for keyword in address_keywords:
            if keyword in text_lower:
                score += 5.0
                indicators.append(f"Address keyword found: {keyword}")
                break
        
        # Normalize score to 0-100
        score = min(100.0, score)
        
        # Consider it a contact page if score >= 40
        is_contact_page = score >= 40.0
        
        return PageAnalysis(
            is_contact_page=is_contact_page,
            confidence_score=score,
            contact_indicators=indicators,
            links_found=[]
        )
    
    def find_contact_page_links(self, html: str, base_url: str) -> List[str]:
        """
        Find links to potential contact pages
        
        Args:
            html: HTML content
            base_url: Base URL for resolving relative links
            
        Returns:
            List of contact page URLs
        """
        if not html or not base_url:
            return []
        
        soup = BeautifulSoup(html, 'html.parser')
        contact_links = []
        seen_urls = set()
        
        # Find all links
        for link in soup.find_all('a', href=True):
            href = link['href']
            link_text = link.get_text().strip().lower()
            
            # Resolve relative URLs
            absolute_url = urljoin(base_url, href)
            
            # Skip if already seen
            if absolute_url in seen_urls:
                continue
            
            # Check if link text contains contact keywords
            is_contact_link = False
            for keyword in self.CONTACT_PAGE_KEYWORDS:
                if keyword in link_text or keyword in href.lower():
                    is_contact_link = True
                    break
            
            # Check if URL matches contact patterns
            if not is_contact_link:
                if self.contact_url_regex.search(href.lower()):
                    is_contact_link = True
            
            if is_contact_link:
                # Ensure it's from the same domain
                if self._is_same_domain(base_url, absolute_url):
                    contact_links.append(absolute_url)
                    seen_urls.add(absolute_url)
        
        return contact_links
    
    def extract_structured_contact(self, html: str) -> Dict[str, any]:
        """
        Extract structured contact information from HTML
        
        Args:
            html: HTML content
            
        Returns:
            Dictionary with structured contact data
        """
        if not html:
            return {}
        
        soup = BeautifulSoup(html, 'html.parser')
        result = {
            'emails': [],
            'phones': [],
            'addresses': [],
            'social_media': []
        }
        
        # Extract contact info
        contact_info = self.parse_html(html)
        result['emails'] = contact_info.emails
        result['phones'] = contact_info.whatsapp_numbers
        
        # Extract social media links
        social_patterns = {
            'facebook': r'facebook\.com/[\w.-]+',
            'instagram': r'instagram\.com/[\w.-]+',
            'twitter': r'twitter\.com/[\w.-]+',
            'linkedin': r'linkedin\.com/[\w.-/]+',
        }
        
        for link in soup.find_all('a', href=True):
            href = link['href']
            for platform, pattern in social_patterns.items():
                if re.search(pattern, href, re.IGNORECASE):
                    result['social_media'].append({
                        'platform': platform,
                        'url': href
                    })
        
        # Extract addresses (basic implementation)
        address_tags = soup.find_all(['address', 'div', 'p'], class_=re.compile(r'address|alamat|location|lokasi', re.IGNORECASE))
        for tag in address_tags:
            text = tag.get_text(strip=True)
            if len(text) > 20 and len(text) < 500:  # Reasonable address length
                result['addresses'].append(text)
        
        return result
    
    def _extract_priority_sections(self, soup: BeautifulSoup) -> str:
        """
        Extract text from priority sections
        
        Args:
            soup: BeautifulSoup object
            
        Returns:
            Combined text from priority sections
        """
        priority_text = []
        
        # Extract from footer
        footers = soup.find_all('footer')
        for footer in footers:
            priority_text.append(footer.get_text(separator=' ', strip=True))
        
        # Extract from elements with contact-related classes/ids
        contact_elements = soup.find_all(
            ['div', 'section', 'aside'],
            class_=re.compile(r'contact|kontak|hubungi|footer|address|alamat', re.IGNORECASE)
        )
        for element in contact_elements:
            priority_text.append(element.get_text(separator=' ', strip=True))
        
        # Extract from elements with contact-related ids
        contact_ids = soup.find_all(
            ['div', 'section', 'aside'],
            id=re.compile(r'contact|kontak|hubungi|footer|address|alamat', re.IGNORECASE)
        )
        for element in contact_ids:
            priority_text.append(element.get_text(separator=' ', strip=True))
        
        return ' '.join(priority_text)
    
    def _extract_mailto_links(self, soup: BeautifulSoup) -> List[str]:
        """
        Extract email addresses from mailto links
        
        Args:
            soup: BeautifulSoup object
            
        Returns:
            List of email addresses
        """
        emails = []
        mailto_links = soup.find_all('a', href=re.compile(r'^mailto:', re.IGNORECASE))
        
        for link in mailto_links:
            href = link['href']
            # Extract email from mailto:email@domain.com
            email = href.replace('mailto:', '').split('?')[0].strip()
            if email:
                emails.append(email.lower())
        
        return emails
    
    def _extract_tel_links(self, soup: BeautifulSoup) -> List[str]:
        """
        Extract phone numbers from tel links
        
        Args:
            soup: BeautifulSoup object
            
        Returns:
            List of phone numbers
        """
        numbers = []
        tel_links = soup.find_all('a', href=re.compile(r'^tel:', re.IGNORECASE))
        
        for link in tel_links:
            href = link['href']
            # Extract number from tel:+62xxx
            number = href.replace('tel:', '').strip()
            # Standardize using contact extractor
            standardized = self.contact_extractor._standardize_phone_number(number)
            if standardized:
                numbers.append(standardized)
        
        return numbers
    
    def _is_same_domain(self, base_url: str, target_url: str) -> bool:
        """
        Check if two URLs are from the same domain
        
        Args:
            base_url: Base URL
            target_url: Target URL to check
            
        Returns:
            True if same domain, False otherwise
        """
        try:
            base_domain = urlparse(base_url).netloc
            target_domain = urlparse(target_url).netloc
            return base_domain == target_domain
        except Exception:
            return False


# Alias for backward compatibility
HTMLContactParser = HTMLParser
