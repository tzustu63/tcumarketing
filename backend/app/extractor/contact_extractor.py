"""
Contact Information Extractor
"""
import re
from typing import List, Optional, Dict
from dataclasses import dataclass
from app.extractor.institution_classifier import InstitutionClassifier


@dataclass
class ContactInfo:
    """Contact information data class"""
    emails: List[str]
    whatsapp_numbers: List[str]
    raw_text: str
    institution_type: Optional[str] = None
    classification_confidence: Optional[float] = None


class ContactExtractor:
    """
    Extract contact information (Email and WhatsApp) from text
    """
    
    # Email patterns
    EMAIL_PATTERNS = [
        # Basic email format
        r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
        # Indonesian specific domains
        r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.(co\.id|ac\.id|sch\.id|or\.id|go\.id)',
        # Common prefixes
        r'(info|contact|admin|humas|admission|pendaftaran)@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
    ]
    
    # WhatsApp patterns
    WHATSAPP_PATTERNS = [
        # Indonesian phone numbers with +62
        r'\+62\s?8[0-9]{8,11}',
        # Indonesian phone numbers starting with 08
        r'08[0-9]{8,11}',
        # WhatsApp with label
        r'(?:WA|WhatsApp|wa|whatsapp)[\s:：]+(\+62|0)8[0-9]{8,11}',
        # International format with spaces/dashes
        r'\+62[\s-]?8[\s-]?[0-9]{2,4}[\s-]?[0-9]{4,8}',
        # Format: 62 8xxx
        r'62\s?8[0-9]{8,11}',
    ]
    
    # Common email/phone indicators
    CONTACT_INDICATORS = [
        'email', 'e-mail', 'surel',
        'whatsapp', 'wa', 'hp', 'handphone', 'telepon', 'telp', 'phone',
        'kontak', 'hubungi', 'contact'
    ]
    
    def __init__(self):
        """Initialize the contact extractor"""
        # Compile individual patterns
        self.email_regexes = [re.compile(pattern, re.IGNORECASE) for pattern in self.EMAIL_PATTERNS]
        self.whatsapp_regexes = [re.compile(pattern, re.IGNORECASE) for pattern in self.WHATSAPP_PATTERNS]
        # Initialize institution classifier
        self.classifier = InstitutionClassifier()
    
    def extract_emails(self, text: str) -> List[str]:
        """
        Extract email addresses from text
        
        Args:
            text: Input text to extract emails from
            
        Returns:
            List of unique email addresses
        """
        if not text:
            return []
        
        # Find all email matches using all patterns
        all_emails = []
        for regex in self.email_regexes:
            matches = regex.findall(text)
            all_emails.extend(matches)
        
        # Clean and deduplicate
        cleaned_emails = []
        for email in all_emails:
            # Handle tuple results from regex groups
            if isinstance(email, tuple):
                email = email[0] if email[0] else email[1] if len(email) > 1 else ''
            
            email = email.strip().lower()
            
            # Validate email format
            if self._is_valid_email(email) and email not in cleaned_emails:
                cleaned_emails.append(email)
        
        return cleaned_emails
    
    def extract_whatsapp(self, text: str) -> List[str]:
        """
        Extract WhatsApp numbers from text
        
        Args:
            text: Input text to extract WhatsApp numbers from
            
        Returns:
            List of unique WhatsApp numbers in standardized format
        """
        if not text:
            return []
        
        # Find all WhatsApp matches using all patterns
        all_numbers = []
        for regex in self.whatsapp_regexes:
            matches = regex.findall(text)
            all_numbers.extend(matches)
        
        # Clean and standardize
        cleaned_numbers = []
        for number in all_numbers:
            # Handle tuple results from regex groups
            if isinstance(number, tuple):
                number = ''.join(str(n) for n in number if n)
            
            # Standardize format
            standardized = self._standardize_phone_number(str(number))
            
            if standardized and standardized not in cleaned_numbers:
                cleaned_numbers.append(standardized)
        
        return cleaned_numbers
    
    def extract_from_text(self, text: str, institution_name: Optional[str] = None) -> ContactInfo:
        """
        Extract all contact information from text
        
        Args:
            text: Input text to extract contact info from
            institution_name: Optional institution name for classification
            
        Returns:
            ContactInfo object with emails, WhatsApp numbers, and institution type
        """
        # Clean text
        cleaned_text = self._clean_text(text)
        
        # Extract emails and WhatsApp numbers
        emails = self.extract_emails(cleaned_text)
        whatsapp_numbers = self.extract_whatsapp(cleaned_text)
        
        # Classify institution type if name is provided
        institution_type = None
        classification_confidence = None
        if institution_name:
            classification_result = self.classifier.classify(institution_name, cleaned_text)
            if classification_result:
                institution_type = classification_result.institution_type
                classification_confidence = classification_result.confidence
        
        return ContactInfo(
            emails=emails,
            whatsapp_numbers=whatsapp_numbers,
            raw_text=text[:500],  # Store first 500 chars for reference
            institution_type=institution_type,
            classification_confidence=classification_confidence
        )
    
    def _clean_text(self, text: str) -> str:
        """
        Clean and normalize text for extraction
        
        Args:
            text: Input text
            
        Returns:
            Cleaned text
        """
        if not text:
            return ""
        
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove HTML entities
        text = re.sub(r'&[a-z]+;', ' ', text)
        
        # Normalize quotes and dashes
        text = text.replace('"', '"').replace('"', '"')
        text = text.replace('–', '-').replace('—', '-')
        
        return text.strip()
    
    def _is_valid_email(self, email: str) -> bool:
        """
        Validate email format
        
        Args:
            email: Email address to validate
            
        Returns:
            True if valid, False otherwise
        """
        if not email or len(email) < 5:
            return False
        
        # Check for @ symbol
        if '@' not in email:
            return False
        
        # Check for domain
        parts = email.split('@')
        if len(parts) != 2:
            return False
        
        local, domain = parts
        
        # Validate local part
        if not local or len(local) < 1:
            return False
        
        # Validate domain
        if not domain or '.' not in domain:
            return False
        
        # Check for common invalid patterns
        invalid_patterns = [
            r'\.\.', # Double dots
            r'@\.', # @ followed by dot
            r'\.@', # Dot followed by @
            r'\s', # Whitespace
        ]
        
        for pattern in invalid_patterns:
            if re.search(pattern, email):
                return False
        
        return True
    
    def _standardize_phone_number(self, number: str) -> Optional[str]:
        """
        Standardize phone number to +62 format
        
        Args:
            number: Phone number to standardize
            
        Returns:
            Standardized phone number or None if invalid
        """
        if not number:
            return None
        
        # Remove all non-digit characters except +
        cleaned = re.sub(r'[^\d+]', '', number)
        
        # Remove leading zeros and +
        cleaned = cleaned.lstrip('0').lstrip('+')
        
        # Handle different formats
        if cleaned.startswith('62'):
            # Already in 62 format
            phone = cleaned
        elif cleaned.startswith('8'):
            # Add country code
            phone = '62' + cleaned
        else:
            return None
        
        # Validate length (Indonesian mobile: 62 + 8-11 digits)
        if len(phone) < 11 or len(phone) > 14:
            return None
        
        # Validate starts with 628
        if not phone.startswith('628'):
            return None
        
        return '+' + phone
    
    def extract_with_context(self, text: str, context_window: int = 50) -> Dict[str, List[Dict]]:
        """
        Extract contact information with surrounding context
        
        Args:
            text: Input text
            context_window: Number of characters to include as context
            
        Returns:
            Dictionary with emails and whatsapp numbers with context
        """
        results = {
            'emails': [],
            'whatsapp': []
        }
        
        # Extract emails with context
        for regex in self.email_regexes:
            for match in regex.finditer(text):
                email = match.group(0)
                start = max(0, match.start() - context_window)
                end = min(len(text), match.end() + context_window)
                context = text[start:end]
                
                results['emails'].append({
                    'value': email,
                    'context': context,
                    'position': match.start()
                })
        
        # Extract WhatsApp with context
        for regex in self.whatsapp_regexes:
            for match in regex.finditer(text):
                number = match.group(0)
                standardized = self._standardize_phone_number(number)
                if standardized:
                    start = max(0, match.start() - context_window)
                    end = min(len(text), match.end() + context_window)
                    context = text[start:end]
                    
                    results['whatsapp'].append({
                        'value': standardized,
                        'original': number,
                        'context': context,
                        'position': match.start()
                    })
        
        return results
    
    def extract_from_social_media(self, text: str, platform: str) -> ContactInfo:
        """
        Extract contact information from social media content.
        Uses platform-specific patterns and markers.
        
        Args:
            text: Social media bio/description text
            platform: Platform name ('facebook', 'instagram')
            
        Returns:
            ContactInfo object with extracted information
        """
        # Use the standard extraction as base
        return self.extract_from_text(text)
