# Social Media Extraction Module

This module provides functionality to extract contact information from Facebook and Instagram pages/profiles.

## Features

### 1. Facebook Page Scraper (`facebook_scraper.py`)

Extracts contact information from Facebook business pages:

- **Page Information**: Page name, description
- **Contact Details**: Emails, WhatsApp numbers, phone numbers
- **About Section**: Automatically navigates to About section
- **Error Handling**: Handles access restrictions, timeouts, and blocked requests

#### Usage

```python
from app.scraper import ScrapingEngine, FacebookScraper

# Initialize scraping engine
with ScrapingEngine(headless=True, use_anti_detection=True) as engine:
    # Create Facebook scraper
    fb_scraper = FacebookScraper(engine)
    
    # Extract page information
    result = fb_scraper.extract_page_info('https://www.facebook.com/example')
    
    print(f"Page: {result['page_name']}")
    print(f"Emails: {result['emails']}")
    print(f"WhatsApp: {result['whatsapp_numbers']}")
```

#### Result Format

```python
{
    'url': 'https://www.facebook.com/example',
    'platform': 'facebook',
    'page_name': 'Example School',
    'description': 'International school in Jakarta...',
    'emails': ['info@example.com'],
    'whatsapp_numbers': ['+628123456789'],
    'phone_numbers': ['02112345678'],
    'raw_text': 'Full page text...',
    'status': 'success',
    'error': None
}
```

### 2. Instagram Profile Scraper (`instagram_scraper.py`)

Extracts contact information from Instagram business profiles:

- **Profile Information**: Username, bio
- **Contact Details**: Emails, WhatsApp numbers from bio
- **External Links**: Link-in-bio URLs
- **Error Handling**: Handles private profiles, timeouts

#### Usage

```python
from app.scraper import ScrapingEngine, InstagramScraper

# Initialize scraping engine
with ScrapingEngine(headless=True, use_anti_detection=True) as engine:
    # Create Instagram scraper
    ig_scraper = InstagramScraper(engine)
    
    # Extract profile information
    result = ig_scraper.extract_profile_info('https://www.instagram.com/example')
    
    print(f"Username: {result['username']}")
    print(f"Bio: {result['bio']}")
    print(f"Emails: {result['emails']}")
    print(f"WhatsApp: {result['whatsapp_numbers']}")
```

#### Result Format

```python
{
    'url': 'https://www.instagram.com/example',
    'platform': 'instagram',
    'username': 'example',
    'bio': 'International school | Email: info@example.com',
    'external_links': ['https://example.com'],
    'emails': ['info@example.com'],
    'whatsapp_numbers': ['+628123456789'],
    'phone_numbers': [],
    'raw_text': 'Bio and page text...',
    'status': 'success',
    'error': None
}
```

### 3. Social Media Extractor (`social_media_extractor.py`)

Advanced extraction with social media-specific pattern recognition:

- **Marker Detection**: Recognizes "WA:", "Email:", "HP:", etc.
- **Link-in-Bio**: Detects link-in-bio patterns
- **DM Patterns**: Identifies "DM for info" patterns
- **Institution Type**: Automatically categorizes institutions
- **External Links**: Processes wa.me and mailto links

#### Usage

```python
from app.scraper import SocialMediaExtractor

extractor = SocialMediaExtractor()

# Extract with enhanced pattern matching
text = """
SMA Internasional Jakarta
📧 Email: admission@school.co.id
📱 WA: +62 812-3456-7890
Link in bio for more info
"""

result = extractor.extract_from_social_media(
    text=text,
    platform='instagram',
    external_links=['https://wa.me/628123456789']
)

print(f"Emails: {result.emails}")
print(f"WhatsApp: {result.whatsapp_numbers}")
print(f"Markers found: {result.markers_found}")
```

#### Supported Markers

**WhatsApp Markers:**
- WA:, wa:, Wa:
- WhatsApp:, whatsapp:
- HP:, hp: (Indonesian for handphone)
- Telp:, telp: (Indonesian for telephone)
- Phone:, phone:
- Contact:, contact:
- Hubungi: (Indonesian for contact)
- 📱, ☎️ (emoji markers)

**Email Markers:**
- Email:, email:, E-mail:
- Surel: (Indonesian for email)
- 📧, ✉️ (emoji markers)

**Special Patterns:**
- Link in bio, linkinbio
- DM for info, send DM
- Chat me, hubungi via DM

#### Institution Type Detection

Automatically categorizes institutions based on keywords:

```python
# High school (高中)
text = "SMA Internasional Jakarta"
type = extractor.extract_institution_type_from_social(text)
# Returns: '高中'

# Language center (華語中心)
text = "Pusat Bahasa Mandarin"
type = extractor.extract_institution_type_from_social(text)
# Returns: '華語中心'

# Education agency (代辦)
text = "Agen Pendidikan - Study Abroad"
type = extractor.extract_institution_type_from_social(text)
# Returns: '代辦'
```

## Extraction Patterns

### Email Patterns

```regex
# Basic email format
[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}

# Indonesian specific domains
.*@.*\.(co\.id|ac\.id|sch\.id|or\.id|go\.id)

# Common prefixes
(info|contact|admin|humas|admission|pendaftaran)@.*
```

### WhatsApp Patterns

```regex
# Indonesian phone numbers with +62
\+62\s?8[0-9]{8,11}

# Indonesian phone numbers starting with 08
08[0-9]{8,11}

# WhatsApp with label
(?:WA|WhatsApp|wa)[\s:：]+(\+62|0)8[0-9]{8,11}

# International format with spaces/dashes
\+62[\s-]?8[\s-]?[0-9]{2,4}[\s-]?[0-9]{4,8}
```

### Phone Number Standardization

All Indonesian phone numbers are standardized to `+62` format:

- `08123456789` → `+628123456789`
- `+62 812-3456-7890` → `+6281234567890`
- `62 812 3456 7890` → `+6281234567890`

## Error Handling

### Common Scenarios

1. **Access Restrictions**: Pages requiring login
2. **Timeouts**: Slow loading pages
3. **No Contact Info**: Pages without public contact information
4. **Rate Limiting**: Too many requests

### Error Result Format

```python
{
    'url': 'https://www.facebook.com/example',
    'platform': 'facebook',
    'status': 'failed',
    'error': 'timeout',
    # All other fields are empty/None
}
```

## Logging

The module provides structured logging for extraction results:

```python
log_entry = extractor.log_extraction_result(
    platform='facebook',
    url='https://facebook.com/example',
    contact=contact_info,
    page_name='Example School'
)

# Log entry format:
{
    'platform': 'facebook',
    'url': 'https://facebook.com/example',
    'page_name': 'Example School',
    'has_contact': True,
    'email_count': 1,
    'whatsapp_count': 1,
    'phone_count': 0,
    'external_links_count': 0,
    'markers_found': ['email_marker', 'whatsapp_marker'],
    'status': 'success'
}
```

## Best Practices

1. **Use Anti-Detection**: Always enable anti-detection measures
   ```python
   engine = ScrapingEngine(headless=True, use_anti_detection=True)
   ```

2. **Handle Errors Gracefully**: Check status before processing results
   ```python
   if result['status'] == 'success':
       # Process contact information
   else:
       # Log error and continue
   ```

3. **Respect Rate Limits**: Use delays between requests
   ```python
   # Anti-detection manager handles this automatically
   ```

4. **Validate Extracted Data**: Use ContactValidator for validation
   ```python
   from app.extractor import ContactValidator
   validator = ContactValidator()
   is_valid = validator.validate_email(email)
   ```

5. **Log Unavailable Contact**: Track pages without contact info
   ```python
   if not result['emails'] and not result['whatsapp_numbers']:
       # Log as "contact_unavailable"
   ```

## Integration with Database

Example of storing extracted information:

```python
from app.repositories import ContactRepository
from app.models import Contact

# Extract information
result = fb_scraper.extract_page_info(url)

if result['status'] == 'success':
    # Create contact record
    contact = Contact(
        institution_name=result['page_name'],
        source_url=result['url'],
        source_platform='facebook',
        email=result['emails'][0] if result['emails'] else None,
        whatsapp=result['whatsapp_numbers'][0] if result['whatsapp_numbers'] else None,
        additional_info={
            'description': result['description'],
            'all_emails': result['emails'],
            'all_whatsapp': result['whatsapp_numbers']
        }
    )
    
    # Save to database
    repo = ContactRepository(db_session)
    repo.create(contact)
```

## Testing

Run the validation tests:

```bash
# Simple pattern validation (no dependencies)
python backend/tests/validate_social_media_simple.py

# Full unit tests (requires pytest)
pytest backend/tests/test_social_media_extraction.py -v
```

## Requirements

- Python 3.11+
- Selenium 4.17+
- BeautifulSoup4 4.12+
- See `backend/requirements.txt` for full list

## Limitations

1. **Authentication**: Cannot access private profiles or pages requiring login
2. **Dynamic Content**: Some content may load dynamically and require additional wait time
3. **Platform Changes**: Social media platforms frequently change their HTML structure
4. **Rate Limiting**: Excessive requests may result in temporary blocks

## Future Enhancements

- [ ] Support for LinkedIn profiles
- [ ] Support for Twitter/X profiles
- [ ] OCR for contact info in images
- [ ] Machine learning for better pattern recognition
- [ ] Proxy rotation for better anti-detection
