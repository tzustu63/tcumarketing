"""
Example usage of social media scrapers.
Demonstrates how to extract contact information from Facebook and Instagram.
"""
import logging
from .scraping_engine import ScrapingEngine
from .facebook_scraper import FacebookScraper
from .instagram_scraper import InstagramScraper
from .social_media_extractor import SocialMediaExtractor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def extract_facebook_contact(url: str):
    """
    Extract contact information from a Facebook page.
    
    Args:
        url: Facebook page URL
    """
    logger.info(f"Extracting Facebook page: {url}")
    
    # Initialize scraping engine
    with ScrapingEngine(headless=True, use_anti_detection=True) as engine:
        # Create Facebook scraper
        fb_scraper = FacebookScraper(engine)
        
        # Extract page information
        result = fb_scraper.extract_page_info(url)
        
        # Process with social media extractor
        sm_extractor = SocialMediaExtractor()
        
        if result['status'] == 'success':
            # Log the extraction result
            log_entry = sm_extractor.log_extraction_result(
                platform='facebook',
                url=url,
                contact=type('obj', (object,), {
                    'emails': result['emails'],
                    'whatsapp_numbers': result['whatsapp_numbers'],
                    'phone_numbers': result['phone_numbers'],
                    'external_links': [],
                    'markers_found': []
                })(),
                page_name=result['page_name']
            )
            
            # Print results
            print(f"\n{'='*60}")
            print(f"Facebook Page: {result['page_name']}")
            print(f"URL: {url}")
            print(f"{'='*60}")
            print(f"Emails: {', '.join(result['emails']) if result['emails'] else 'None'}")
            print(f"WhatsApp: {', '.join(result['whatsapp_numbers']) if result['whatsapp_numbers'] else 'None'}")
            print(f"Phones: {', '.join(result['phone_numbers']) if result['phone_numbers'] else 'None'}")
            print(f"Description: {result['description'][:100] if result['description'] else 'None'}...")
            print(f"{'='*60}\n")
            
            return result
        else:
            logger.error(f"Failed to extract: {result['error']}")
            return None


def extract_instagram_contact(url: str):
    """
    Extract contact information from an Instagram profile.
    
    Args:
        url: Instagram profile URL
    """
    logger.info(f"Extracting Instagram profile: {url}")
    
    # Initialize scraping engine
    with ScrapingEngine(headless=True, use_anti_detection=True) as engine:
        # Create Instagram scraper
        ig_scraper = InstagramScraper(engine)
        
        # Extract profile information
        result = ig_scraper.extract_profile_info(url)
        
        # Process with social media extractor
        sm_extractor = SocialMediaExtractor()
        
        if result['status'] == 'success':
            # Enhanced extraction with social media patterns
            enhanced_contact = sm_extractor.extract_from_social_media(
                text=result['bio'],
                platform='instagram',
                external_links=result['external_links']
            )
            
            # Log the extraction result
            log_entry = sm_extractor.log_extraction_result(
                platform='instagram',
                url=url,
                contact=enhanced_contact,
                page_name=result['username']
            )
            
            # Print results
            print(f"\n{'='*60}")
            print(f"Instagram Profile: @{result['username']}")
            print(f"URL: {url}")
            print(f"{'='*60}")
            print(f"Bio: {result['bio'][:100] if result['bio'] else 'None'}...")
            print(f"Emails: {', '.join(enhanced_contact.emails) if enhanced_contact.emails else 'None'}")
            print(f"WhatsApp: {', '.join(enhanced_contact.whatsapp_numbers) if enhanced_contact.whatsapp_numbers else 'None'}")
            print(f"External Links: {', '.join(result['external_links']) if result['external_links'] else 'None'}")
            print(f"Markers Found: {', '.join(enhanced_contact.markers_found) if enhanced_contact.markers_found else 'None'}")
            print(f"{'='*60}\n")
            
            return result
        else:
            logger.error(f"Failed to extract: {result['error']}")
            return None


def batch_extract_social_media(urls: list):
    """
    Extract contact information from multiple social media URLs.
    
    Args:
        urls: List of social media URLs (Facebook or Instagram)
    """
    results = []
    
    with ScrapingEngine(headless=True, use_anti_detection=True) as engine:
        fb_scraper = FacebookScraper(engine)
        ig_scraper = InstagramScraper(engine)
        sm_extractor = SocialMediaExtractor()
        
        for url in urls:
            try:
                if fb_scraper.is_facebook_url(url):
                    result = fb_scraper.extract_page_info(url)
                    results.append(result)
                elif ig_scraper.is_instagram_url(url):
                    result = ig_scraper.extract_profile_info(url)
                    results.append(result)
                else:
                    logger.warning(f"Unknown platform for URL: {url}")
                    
            except Exception as e:
                logger.error(f"Error processing {url}: {e}")
                continue
    
    return results


if __name__ == "__main__":
    # Example usage
    print("Social Media Contact Extractor - Example Usage\n")
    
    # Example Facebook URL (replace with actual URL)
    # facebook_url = "https://www.facebook.com/example"
    # extract_facebook_contact(facebook_url)
    
    # Example Instagram URL (replace with actual URL)
    # instagram_url = "https://www.instagram.com/example"
    # extract_instagram_contact(instagram_url)
    
    # Example batch processing
    # urls = [
    #     "https://www.facebook.com/example1",
    #     "https://www.instagram.com/example2",
    # ]
    # results = batch_extract_social_media(urls)
    
    print("Please uncomment and provide actual URLs to test the extractors.")
