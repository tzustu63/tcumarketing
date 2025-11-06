"""
Contact Information Validator
"""
import re
from typing import Optional, Tuple
from dataclasses import dataclass
from email.utils import parseaddr


@dataclass
class ValidationResult:
    """Validation result data class"""
    is_valid: bool
    error_message: Optional[str] = None
    normalized_value: Optional[str] = None


class ContactValidator:
    """
    Validate contact information (Email and WhatsApp numbers)
    """
    
    # Indonesian domain patterns
    INDONESIAN_DOMAINS = [
        r'\.co\.id$',
        r'\.ac\.id$',
        r'\.sch\.id$',
        r'\.or\.id$',
        r'\.go\.id$',
        r'\.web\.id$',
    ]
    
    # Common disposable email domains to blacklist
    DISPOSABLE_DOMAINS = [
        'tempmail.com',
        'throwaway.email',
        'guerrillamail.com',
        'mailinator.com',
        '10minutemail.com',
    ]
    
    # Invalid email patterns
    INVALID_EMAIL_PATTERNS = [
        r'noreply@',
        r'no-reply@',
        r'donotreply@',
        r'example@',
        r'test@',
        r'admin@localhost',
    ]
    
    def __init__(self):
        """Initialize the contact validator"""
        self.indonesian_domain_regex = re.compile('|'.join(self.INDONESIAN_DOMAINS), re.IGNORECASE)
    
    def validate_email(self, email: str) -> ValidationResult:
        """
        Validate email format and domain
        
        Args:
            email: Email address to validate
            
        Returns:
            ValidationResult with validation status
        """
        if not email:
            return ValidationResult(
                is_valid=False,
                error_message="Email is empty"
            )
        
        # Normalize email
        email = email.strip().lower()
        
        # Basic format check
        if '@' not in email:
            return ValidationResult(
                is_valid=False,
                error_message="Email missing @ symbol"
            )
        
        # Split into local and domain parts
        try:
            local, domain = email.rsplit('@', 1)
        except ValueError:
            return ValidationResult(
                is_valid=False,
                error_message="Invalid email format"
            )
        
        # Validate local part
        if not local or len(local) < 1 or len(local) > 64:
            return ValidationResult(
                is_valid=False,
                error_message="Invalid local part length"
            )
        
        # Validate domain part
        if not domain or '.' not in domain:
            return ValidationResult(
                is_valid=False,
                error_message="Invalid domain format"
            )
        
        # Check domain length
        if len(domain) > 255:
            return ValidationResult(
                is_valid=False,
                error_message="Domain too long"
            )
        
        # Check for invalid patterns
        for pattern in self.INVALID_EMAIL_PATTERNS:
            if re.search(pattern, email, re.IGNORECASE):
                return ValidationResult(
                    is_valid=False,
                    error_message="Email matches invalid pattern"
                )
        
        # Check for disposable domains
        if domain in self.DISPOSABLE_DOMAINS:
            return ValidationResult(
                is_valid=False,
                error_message="Disposable email domain"
            )
        
        # Check for consecutive dots
        if '..' in email:
            return ValidationResult(
                is_valid=False,
                error_message="Email contains consecutive dots"
            )
        
        # Check for leading/trailing dots
        if local.startswith('.') or local.endswith('.'):
            return ValidationResult(
                is_valid=False,
                error_message="Local part has leading or trailing dot"
            )
        
        # Validate characters
        valid_local_chars = re.compile(r'^[a-zA-Z0-9._%+-]+$')
        if not valid_local_chars.match(local):
            return ValidationResult(
                is_valid=False,
                error_message="Local part contains invalid characters"
            )
        
        # Validate domain characters
        valid_domain_chars = re.compile(r'^[a-zA-Z0-9.-]+$')
        if not valid_domain_chars.match(domain):
            return ValidationResult(
                is_valid=False,
                error_message="Domain contains invalid characters"
            )
        
        # Check TLD length
        tld = domain.split('.')[-1]
        if len(tld) < 2:
            return ValidationResult(
                is_valid=False,
                error_message="Invalid TLD"
            )
        
        return ValidationResult(
            is_valid=True,
            normalized_value=email
        )
    
    def validate_phone(self, phone: str, country: str = "ID") -> ValidationResult:
        """
        Validate phone number format
        
        Args:
            phone: Phone number to validate
            country: Country code (default: ID for Indonesia)
            
        Returns:
            ValidationResult with validation status
        """
        if not phone:
            return ValidationResult(
                is_valid=False,
                error_message="Phone number is empty"
            )
        
        # Remove whitespace
        phone = phone.strip()
        
        # For Indonesian numbers
        if country == "ID":
            return self._validate_indonesian_phone(phone)
        
        return ValidationResult(
            is_valid=False,
            error_message=f"Validation for country {country} not implemented"
        )
    
    def _validate_indonesian_phone(self, phone: str) -> ValidationResult:
        """
        Validate Indonesian phone number
        
        Args:
            phone: Phone number to validate
            
        Returns:
            ValidationResult with validation status
        """
        # Remove all non-digit characters except +
        cleaned = re.sub(r'[^\d+]', '', phone)
        
        # Check if empty after cleaning
        if not cleaned:
            return ValidationResult(
                is_valid=False,
                error_message="No digits found in phone number"
            )
        
        # Normalize to +62 format
        if cleaned.startswith('+62'):
            normalized = cleaned
        elif cleaned.startswith('62'):
            normalized = '+' + cleaned
        elif cleaned.startswith('08'):
            normalized = '+62' + cleaned[1:]
        elif cleaned.startswith('8'):
            normalized = '+62' + cleaned
        else:
            return ValidationResult(
                is_valid=False,
                error_message="Phone number doesn't match Indonesian format"
            )
        
        # Validate length (Indonesian mobile: +62 + 9-12 digits)
        # Format: +628xxxxxxxxx (minimum 11 chars, maximum 14 chars)
        if len(normalized) < 12 or len(normalized) > 15:
            return ValidationResult(
                is_valid=False,
                error_message=f"Invalid phone number length: {len(normalized)}"
            )
        
        # Validate starts with +628 (Indonesian mobile)
        if not normalized.startswith('+628'):
            return ValidationResult(
                is_valid=False,
                error_message="Indonesian mobile numbers must start with +628"
            )
        
        # Validate all characters after + are digits
        if not normalized[1:].isdigit():
            return ValidationResult(
                is_valid=False,
                error_message="Phone number contains non-digit characters"
            )
        
        return ValidationResult(
            is_valid=True,
            normalized_value=normalized
        )
    
    def calculate_quality_score(
        self,
        has_email: bool,
        has_whatsapp: bool,
        source_platform: str,
        email_valid: bool = True,
        phone_valid: bool = True,
        has_institution_name: bool = True
    ) -> float:
        """
        Calculate data quality score (0-100)
        
        Scoring criteria:
        - Has valid email: +40
        - Has valid WhatsApp: +40
        - Source is official website: +10
        - Has institution name: +10
        
        Args:
            has_email: Whether email is present
            has_whatsapp: Whether WhatsApp number is present
            source_platform: Source platform (website, facebook, instagram)
            email_valid: Whether email is valid (default: True)
            phone_valid: Whether phone is valid (default: True)
            has_institution_name: Whether institution name is present (default: True)
            
        Returns:
            Quality score between 0 and 100
        """
        score = 0.0
        
        # Email score (40 points)
        if has_email and email_valid:
            score += 40.0
        elif has_email and not email_valid:
            score += 20.0  # Partial credit for having email even if invalid
        
        # WhatsApp score (40 points)
        if has_whatsapp and phone_valid:
            score += 40.0
        elif has_whatsapp and not phone_valid:
            score += 20.0  # Partial credit for having phone even if invalid
        
        # Source platform score (10 points)
        if source_platform.lower() == 'website':
            score += 10.0
        elif source_platform.lower() in ['facebook', 'instagram']:
            score += 5.0  # Partial credit for social media
        
        # Institution name score (10 points)
        if has_institution_name:
            score += 10.0
        
        # Ensure score is between 0 and 100
        return min(100.0, max(0.0, score))
    
    def is_indonesian_domain(self, email: str) -> bool:
        """
        Check if email has Indonesian domain
        
        Args:
            email: Email address to check
            
        Returns:
            True if Indonesian domain, False otherwise
        """
        if not email or '@' not in email:
            return False
        
        domain = email.split('@')[-1].lower()
        return bool(self.indonesian_domain_regex.search(domain))
    
    def validate_contact_info(
        self,
        email: Optional[str] = None,
        whatsapp: Optional[str] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate complete contact information
        
        Args:
            email: Email address (optional)
            whatsapp: WhatsApp number (optional)
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # At least one contact method must be provided
        if not email and not whatsapp:
            return False, "At least one contact method (email or WhatsApp) is required"
        
        # Validate email if provided
        if email:
            email_result = self.validate_email(email)
            if not email_result.is_valid:
                return False, f"Invalid email: {email_result.error_message}"
        
        # Validate WhatsApp if provided
        if whatsapp:
            phone_result = self.validate_phone(whatsapp)
            if not phone_result.is_valid:
                return False, f"Invalid WhatsApp: {phone_result.error_message}"
        
        return True, None
