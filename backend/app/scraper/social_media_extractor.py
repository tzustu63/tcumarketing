"""
Social Media Contact Extractor
Handles social media specific contact information formats and patterns.
"""
import re
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from app.extractor.institution_classifier import InstitutionClassifier

logger = logging.getLogger(__name__)


@dataclass
class SocialMediaContact:
    """Social media contact information"""
    emails: List[str]
    whatsapp_numbers: List[str]
    phone_numbers: List[str]
    external_links: List[str]
    raw_text: str
    markers_found: List[str]  # Track which markers were found (WA:, Email:, etc.)


class SocialMediaExtractor:
    """
    Extractor for social media specific contact information formats.
    Handles patterns like "WA:", "Email:", "DM for info", link-in-bio, etc.
    """
    
    # Social media specific markers
    WHATSAPP_MARKERS = [
        r'(?:WA|wa|Wa)[\s:：]+',
        r'(?:WhatsApp|whatsapp|Whatsapp)[\s:：]+',
        r'(?:HP|hp|Hp)[\s:：]+',
        r'(?:Telp|telp|TELP)[\s:：]+',
        r'(?:Phone|phone|PHONE)[\s:：]+',
        r'(?:Contact|contact|CONTACT)[\s:：]+',
        r'(?:Hubungi|hubungi)[\s:：]+',
        r'📱[\s:：]*',
        r'☎️[\s:：]*',
    ]
    
    EMAIL_MARKERS = [
        r'(?:Email|email|E-mail|e-mail|EMAIL)[\s:：]+',
        r'(?:Surel|surel)[\s:：]+',
        r'📧[\s:：]*',
        r'✉️[\s:：]*',
    ]
    
    LINK_IN_BIO_PATTERNS = [
        r'link\s+in\s+bio',
        r'linkinbio',
        r'link\s+di\s+bio',
        r'cek\s+bio',
        r'see\s+bio',
        r'bio\s+link',
    ]
    
    DM_PATTERNS = [
        r'DM\s+(?:for|untuk|me)',
        r'(?:send|kirim)\s+DM',
        r'chat\s+(?:me|kami)',
        r'hubungi\s+via\s+DM',
    ]
    
    def __init__(self):
        """Initialize the social media extractor"""
        # Compile regex patterns
        self.wa_marker_regex = re.compile('|'.join(self.WHATSAPP_MARKERS), re.IGNORECASE)
        self.email_marker_regex = re.compile('|'.join(self.EMAIL_MARKERS), re.IGNORECASE)
        self.link_in_bio_regex = re.compile('|'.join(self.LINK_IN_BIO_PATTERNS), re.IGNORECASE)
        self.dm_regex = re.compile('|'.join(self.DM_PATTERNS), re.IGNORECASE)
        # Initialize institution classifier
        self.classifier = InstitutionClassifier()
    
    def extract_from_social_media(
        self,
        text: str,
        platform: str,
        external_links: Optional[List[str]] = None
    ) -> SocialMediaContact:
        """
        Extract contact information from social media text with platform-specific handling.
        
        Args:
            text: Text content from social media profile/page
            platform: Platform name ('facebook', 'instagram')
            external_links: List of external links found on the profile
            
        Returns:
            SocialMediaContact object with extracted information
        """
        if not text:
            return self._empty_contact()
        
        markers_found = []
        
        # Extract emails with markers
        emails = self._extract_emails_with_markers(text, markers_found)
        
        # Extract WhatsApp with markers
        whatsapp_numbers = self._extract_whatsapp_with_markers(text, markers_found)
        
        # Extract phone numbers
        phone_numbers = self._extract_phones(text)
        
        # Process external links for contact info
        processed_links = []
        if external_links:
            processed_links = self._process_external_links(external_links, whatsapp_numbers, emails)
        
        # Check for link-in-bio patterns
        if self.link_in_bio_regex.search(text):
            markers_found.append('link_in_bio')
        
        # Check for DM patterns
        if self.dm_regex.search(text):
            markers_found.append('dm_only')
        
        return SocialMediaContact(
            emails=emails,
            whatsapp_numbers=whatsapp_numbers,
            phone_numbers=phone_numbers,
            external_links=processed_links,
            raw_text=text[:1000],
            markers_found=markers_found
        )
    
    def _extract_emails_with_markers(self, text: str, markers_found: List[str]) -> List[str]:
        """
        Extract emails, prioritizing those with markers.
        
        Args:
            text: Input text
            markers_found: List to append found markers to
            
        Returns:
            List of email addresses
        """
        emails = []
        
        # Look for email markers
        for match in self.email_marker_regex.finditer(text):
            markers_found.append('email_marker')
            # Extract text after marker (next 50 chars)
            start = match.end()
            snippet = text[start:start + 50]
            
            # Find email in snippet
            email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
            email_matches = re.findall(email_pattern, snippet)
            emails.extend(email_matches)
        
        # Also extract all emails from full text
        from ..extractor.contact_extractor import ContactExtractor
        extractor = ContactExtractor()
        all_emails = extractor.extract_emails(text)
        
        # Merge and deduplicate
        for email in all_emails:
            if email not in emails:
                emails.append(email)
        
        return emails
    
    def _extract_whatsapp_with_markers(self, text: str, markers_found: List[str]) -> List[str]:
        """
        Extract WhatsApp numbers, prioritizing those with markers.
        
        Args:
            text: Input text
            markers_found: List to append found markers to
            
        Returns:
            List of WhatsApp numbers
        """
        whatsapp_numbers = []
        
        # Look for WhatsApp markers
        for match in self.wa_marker_regex.finditer(text):
            markers_found.append('whatsapp_marker')
            # Extract text after marker (next 30 chars)
            start = match.end()
            snippet = text[start:start + 30]
            
            # Find phone number in snippet
            phone_pattern = r'(\+62|62|0)[\s-]?8[\s-]?[0-9]{2,4}[\s-]?[0-9]{4,8}'
            phone_matches = re.findall(phone_pattern, snippet)
            
            # Standardize numbers
            from ..extractor.contact_extractor import ContactExtractor
            extractor = ContactExtractor()
            for number in phone_matches:
                if isinstance(number, tuple):
                    number = ''.join(number)
                standardized = extractor._standardize_phone_number(number)
                if standardized and standardized not in whatsapp_numbers:
                    whatsapp_numbers.append(standardized)
        
        # Also extract all WhatsApp numbers from full text
        from ..extractor.contact_extractor import ContactExtractor
        extractor = ContactExtractor()
        all_wa = extractor.extract_whatsapp(text)
        
        # Merge and deduplicate
        for wa in all_wa:
            if wa not in whatsapp_numbers:
                whatsapp_numbers.append(wa)
        
        return whatsapp_numbers
    
    def _extract_phones(self, text: str) -> List[str]:
        """
        Extract general phone numbers (non-WhatsApp).
        
        Args:
            text: Input text
            
        Returns:
            List of phone numbers
        """
        phones = []
        
        # Pattern for general phone numbers (not starting with 08 or +62)
        phone_patterns = [
            r'\+[0-9]{1,3}[\s-]?[0-9]{2,4}[\s-]?[0-9]{4,8}',  # International
            r'\([0-9]{2,4}\)[\s-]?[0-9]{4,8}',  # With area code
        ]
        
        for pattern in phone_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                # Skip if it looks like Indonesian mobile (WhatsApp)
                if not any(x in match for x in ['+62', '62', '08']):
                    clean = re.sub(r'[^\d+]', '', match)
                    if clean and clean not in phones:
                        phones.append(match.strip())
        
        return phones
    
    def _process_external_links(
        self,
        links: List[str],
        whatsapp_numbers: List[str],
        emails: List[str]
    ) -> List[str]:
        """
        Process external links to extract contact information.
        
        Args:
            links: List of external URLs
            whatsapp_numbers: List to append found WhatsApp numbers to
            emails: List to append found emails to
            
        Returns:
            List of processed links
        """
        processed = []
        
        for link in links:
            # Check for wa.me links
            if 'wa.me' in link.lower():
                match = re.search(r'wa\.me/(\+?[\d]+)', link)
                if match:
                    number = match.group(1)
                    if not number.startswith('+'):
                        number = '+' + number
                    if number not in whatsapp_numbers:
                        whatsapp_numbers.append(number)
            
            # Check for mailto links
            elif link.startswith('mailto:'):
                email = link.replace('mailto:', '').split('?')[0].strip()
                if email and email not in emails:
                    emails.append(email)
            
            # Keep other links
            else:
                processed.append(link)
        
        return processed
    
    def has_contact_unavailable_indicators(self, text: str) -> bool:
        """
        Check if text indicates contact information is not available.
        
        Args:
            text: Text to check
            
        Returns:
            True if contact unavailable indicators found
        """
        unavailable_patterns = [
            r'no\s+contact',
            r'tidak\s+ada\s+kontak',
            r'private',
            r'pribadi',
            r'DM\s+only',
            r'hanya\s+DM',
        ]
        
        for pattern in unavailable_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        
        return False
    
    def extract_institution_type_from_social(self, text: str, page_name: str = "") -> Optional[str]:
        """
        Extract institution type from social media content using the classifier.
        
        Args:
            text: Bio/description text
            page_name: Page/profile name
            
        Returns:
            Institution type or None
        """
        # Use the classifier for consistent classification
        result = self.classifier.classify(page_name, text)
        
        if result:
            return result.institution_type
        
        return None
    
    def _empty_contact(self) -> SocialMediaContact:
        """Create an empty contact result."""
        return SocialMediaContact(
            emails=[],
            whatsapp_numbers=[],
            phone_numbers=[],
            external_links=[],
            raw_text='',
            markers_found=[]
        )
    
    def log_extraction_result(
        self,
        platform: str,
        url: str,
        contact: SocialMediaContact,
        page_name: str = ""
    ) -> Dict[str, Any]:
        """
        Create a structured log entry for extraction results.
        
        Args:
            platform: Social media platform
            url: Profile/page URL
            contact: Extracted contact information
            page_name: Name of the page/profile
            
        Returns:
            Dictionary with log information
        """
        has_contact = len(contact.emails) > 0 or len(contact.whatsapp_numbers) > 0
        
        log_entry = {
            'platform': platform,
            'url': url,
            'page_name': page_name,
            'has_contact': has_contact,
            'email_count': len(contact.emails),
            'whatsapp_count': len(contact.whatsapp_numbers),
            'phone_count': len(contact.phone_numbers),
            'external_links_count': len(contact.external_links),
            'markers_found': contact.markers_found,
            'status': 'success' if has_contact else 'no_contact_found'
        }
        
        if not has_contact:
            if 'dm_only' in contact.markers_found:
                log_entry['reason'] = 'dm_only'
            elif 'link_in_bio' in contact.markers_found:
                log_entry['reason'] = 'link_in_bio'
            else:
                log_entry['reason'] = 'no_public_contact'
        
        logger.info(f"Social media extraction: {log_entry}")
        return log_entry
