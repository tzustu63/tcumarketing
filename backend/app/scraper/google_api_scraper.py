"""
Google Custom Search API scraper
Uses Google's official API instead of web scraping
"""
import logging
import requests
from typing import List, Optional
from dataclasses import dataclass

from app.config import settings

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """Represents a single search result."""
    url: str
    title: str
    description: str
    position: int
    platform: str = "website"


class GoogleAPISearcher:
    """
    Google Custom Search API client
    More reliable and faster than web scraping
    """
    
    def __init__(self, api_key: str = None, cse_id: str = None):
        """
        Initialize Google API searcher
        
        Args:
            api_key: Google API key
            cse_id: Custom Search Engine ID
        """
        self.api_key = api_key or settings.GOOGLE_API_KEY
        self.cse_id = cse_id or settings.GOOGLE_CSE_ID
        self.base_url = "https://customsearch.googleapis.com/customsearch/v1"
        
        if not self.api_key or not self.cse_id:
            raise ValueError("Google API key and CSE ID are required")
        
        logger.info(f"GoogleAPISearcher initialized with CSE ID: {self.cse_id[:10]}...")
    
    def search(
        self,
        query: str,
        max_results: int = 10,
        country_code: str = "ID",
        language: str = "id"
    ) -> List[SearchResult]:
        """
        Execute a Google Custom Search
        
        Args:
            query: Search query string
            max_results: Maximum number of results to return (max 100)
            country_code: Two-letter country code for geolocation
            language: Language code for results
            
        Returns:
            List of SearchResult objects
        """
        all_results = []
        
        # Google API returns max 10 results per request
        # We need to paginate to get more results
        num_requests = min(10, (max_results + 9) // 10)  # Max 10 requests (100 results)
        
        for page in range(num_requests):
            start_index = page * 10 + 1
            
            try:
                results = self._fetch_page(
                    query=query,
                    start=start_index,
                    num=min(10, max_results - len(all_results)),
                    gl=country_code.lower(),
                    hl=language
                )
                
                if not results:
                    logger.info(f"No more results at page {page + 1}")
                    break
                
                all_results.extend(results)
                logger.info(f"Fetched page {page + 1}: {len(results)} results (total: {len(all_results)})")
                
                if len(all_results) >= max_results:
                    break
                    
            except Exception as e:
                logger.error(f"Error fetching page {page + 1}: {e}")
                break
        
        # Limit to max_results
        all_results = all_results[:max_results]
        
        logger.info(f"Total results fetched: {len(all_results)}/{max_results}")
        return all_results
    
    def _fetch_page(
        self,
        query: str,
        start: int = 1,
        num: int = 10,
        gl: str = "id",
        hl: str = "id"
    ) -> List[SearchResult]:
        """
        Fetch a single page of search results
        
        Args:
            query: Search query
            start: Start index (1-based)
            num: Number of results per page (1-10)
            gl: Geolocation (country code)
            hl: Interface language
            
        Returns:
            List of SearchResult objects
        """
        params = {
            "key": self.api_key,
            "cx": self.cse_id,
            "q": query,
            "start": start,
            "num": num,
            "gl": gl,
            "hl": hl,
        }
        
        try:
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # Check for errors
            if "error" in data:
                error_code = data["error"].get("code", "Unknown")
                error_msg = data["error"].get("message", "Unknown error")
                logger.error(f"Google API error {error_code}: {error_msg}")
                
                # Check if API is not enabled
                if error_code == 403 and "not been used" in error_msg:
                    logger.warning("Google Custom Search API is not enabled. Please enable it in Google Cloud Console.")
                    logger.warning("Visit: https://console.developers.google.com/apis/api/customsearch.googleapis.com/overview")
                
                return []
            
            # Parse results
            items = data.get("items", [])
            results = []
            
            for idx, item in enumerate(items):
                try:
                    result = SearchResult(
                        url=item.get("link", ""),
                        title=item.get("title", ""),
                        description=item.get("snippet", ""),
                        position=start + idx,
                        platform=self._identify_platform(item.get("link", ""))
                    )
                    
                    # Filter out invalid URLs
                    if result.url and result.url.startswith("http"):
                        results.append(result)
                        
                except Exception as e:
                    logger.debug(f"Failed to parse result {idx}: {e}")
                    continue
            
            return results
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return []
    
    def _identify_platform(self, url: str) -> str:
        """
        Identify the platform based on URL
        
        Args:
            url: URL to check
            
        Returns:
            Platform name (website, facebook, instagram)
        """
        if not url:
            return "website"
        
        url_lower = url.lower()
        
        if "facebook.com" in url_lower or "fb.com" in url_lower:
            return "facebook"
        elif "instagram.com" in url_lower:
            return "instagram"
        else:
            return "website"
