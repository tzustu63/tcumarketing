"""
Example usage of the scraping engine.
This file demonstrates how to use the scraping components.
"""
import logging
from scraping_engine import ScrapingEngine
from google_scraper import GoogleScraper
from contact_page_finder import ContactPageFinder

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def example_google_search():
    """Example: Search Google and extract results."""
    logger.info("=== Google Search Example ===")
    
    # Create scraping engine with anti-detection enabled
    with ScrapingEngine(headless=True, use_anti_detection=True) as engine:
        # Create Google scraper
        scraper = GoogleScraper(engine)
        
        # Perform search
        query = "SMA Internasional Jakarta"
        results = scraper.search_google(query, max_pages=2)
        
        # Display results
        logger.info(f"Found {len(results)} results for '{query}'")
        for result in results[:5]:  # Show first 5
            logger.info(f"{result.position}. {result.title}")
            logger.info(f"   URL: {result.url}")
            logger.info(f"   Platform: {result.platform}")
            logger.info(f"   Description: {result.description[:100]}...")
            logger.info("")


def example_contact_page_finder():
    """Example: Find contact page on a website."""
    logger.info("=== Contact Page Finder Example ===")
    
    with ScrapingEngine(headless=True, use_anti_detection=True) as engine:
        finder = ContactPageFinder(engine)
        
        # Try to find contact page
        test_url = "https://example.com"
        contact_url = finder.find_contact_page(test_url)
        
        if contact_url:
            logger.info(f"Found contact page: {contact_url}")
        else:
            logger.info("Could not find contact page")


def example_fetch_with_retry():
    """Example: Fetch a page with automatic retry."""
    logger.info("=== Fetch with Retry Example ===")
    
    with ScrapingEngine(headless=True, use_anti_detection=True) as engine:
        try:
            # Fetch page with retry logic
            page = engine.fetch_page_with_retry("https://example.com")
            logger.info(f"Successfully fetched: {page.title}")
            logger.info(f"URL: {page.url}")
            logger.info(f"HTML length: {len(page.html)} characters")
        except Exception as e:
            logger.error(f"Failed to fetch page: {e}")


if __name__ == "__main__":
    # Run examples (commented out to avoid actual web requests)
    # Uncomment to test
    
    # example_google_search()
    # example_contact_page_finder()
    # example_fetch_with_retry()
    
    logger.info("Examples are commented out. Uncomment to run.")
