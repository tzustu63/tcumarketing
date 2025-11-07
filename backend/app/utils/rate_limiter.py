"""
Rate Limiting and Request Control Module

Provides centralized rate limiting for web scraping operations to ensure
we don't overwhelm target websites and comply with requirement 7.5.
"""
import time
import logging
from typing import Dict, Optional
from datetime import datetime, timedelta
from threading import Lock
from collections import defaultdict
from redis import Redis
from app.config import settings

logger = logging.getLogger(__name__)


class DomainRateLimiter:
    """
    Per-domain rate limiter to control request frequency to specific domains.
    Ensures we don't overwhelm individual websites.
    """
    
    def __init__(
        self,
        redis_client: Optional[Redis] = None,
        max_requests_per_domain: int = 10,
        time_window_seconds: int = 60,
        min_request_interval: float = 2.0
    ):
        """
        Initialize domain-based rate limiter.
        
        Args:
            redis_client: Redis client for distributed rate limiting
            max_requests_per_domain: Max requests per domain in time window
            time_window_seconds: Time window in seconds
            min_request_interval: Minimum seconds between requests to same domain
        """
        self.redis_client = redis_client
        self.max_requests_per_domain = max_requests_per_domain
        self.time_window_seconds = time_window_seconds
        self.min_request_interval = min_request_interval
        
        # Local storage for non-distributed mode
        self._local_requests: Dict[str, list] = defaultdict(list)
        self._local_last_request: Dict[str, float] = {}
        self._lock = Lock()
        
        logger.info(
            f"DomainRateLimiter initialized: "
            f"{max_requests_per_domain} req/{time_window_seconds}s per domain, "
            f"min interval: {min_request_interval}s"
        )
    
    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL."""
        from urllib.parse import urlparse
        parsed = urlparse(url)
        return parsed.netloc or parsed.path.split('/')[0]
    
    def wait_if_needed(self, url: str) -> float:
        """
        Wait if rate limit would be exceeded for the domain.
        
        Args:
            url: URL to check rate limit for
            
        Returns:
            Time waited in seconds
        """
        domain = self._extract_domain(url)
        
        if self.redis_client:
            return self._wait_if_needed_distributed(domain)
        else:
            return self._wait_if_needed_local(domain)
    
    def _wait_if_needed_local(self, domain: str) -> float:
        """Local (non-distributed) rate limiting."""
        with self._lock:
            now = time.time()
            wait_time = 0.0
            
            # Check minimum interval since last request
            if domain in self._local_last_request:
                elapsed = now - self._local_last_request[domain]
                if elapsed < self.min_request_interval:
                    interval_wait = self.min_request_interval - elapsed
                    logger.debug(
                        f"Waiting {interval_wait:.2f}s for min interval to {domain}"
                    )
                    time.sleep(interval_wait)
                    wait_time += interval_wait
                    now = time.time()
            
            # Clean old requests outside time window
            cutoff = now - self.time_window_seconds
            self._local_requests[domain] = [
                req_time for req_time in self._local_requests[domain]
                if req_time > cutoff
            ]
            
            # Check if we've hit the rate limit
            if len(self._local_requests[domain]) >= self.max_requests_per_domain:
                oldest_request = min(self._local_requests[domain])
                window_wait = self.time_window_seconds - (now - oldest_request) + 0.1
                
                if window_wait > 0:
                    logger.info(
                        f"Rate limit reached for {domain}. "
                        f"Waiting {window_wait:.2f}s..."
                    )
                    time.sleep(window_wait)
                    wait_time += window_wait
                    now = time.time()
                    
                    # Clean up again after waiting
                    cutoff = now - self.time_window_seconds
                    self._local_requests[domain] = [
                        req_time for req_time in self._local_requests[domain]
                        if req_time > cutoff
                    ]
            
            # Record this request
            self._local_requests[domain].append(now)
            self._local_last_request[domain] = now
            
            return wait_time
    
    def _wait_if_needed_distributed(self, domain: str) -> float:
        """Distributed rate limiting using Redis."""
        now = time.time()
        wait_time = 0.0
        
        # Redis keys
        requests_key = f"rate_limit:requests:{domain}"
        last_request_key = f"rate_limit:last:{domain}"
        
        try:
            # Check minimum interval
            last_request = self.redis_client.get(last_request_key)
            if last_request:
                elapsed = now - float(last_request)
                if elapsed < self.min_request_interval:
                    interval_wait = self.min_request_interval - elapsed
                    logger.debug(
                        f"Waiting {interval_wait:.2f}s for min interval to {domain}"
                    )
                    time.sleep(interval_wait)
                    wait_time += interval_wait
                    now = time.time()
            
            # Use Redis sorted set for time-windowed rate limiting
            # Remove old entries
            cutoff = now - self.time_window_seconds
            self.redis_client.zremrangebyscore(requests_key, 0, cutoff)
            
            # Check current count
            current_count = self.redis_client.zcard(requests_key)
            
            if current_count >= self.max_requests_per_domain:
                # Get oldest request time
                oldest = self.redis_client.zrange(requests_key, 0, 0, withscores=True)
                if oldest:
                    oldest_time = oldest[0][1]
                    window_wait = self.time_window_seconds - (now - oldest_time) + 0.1
                    
                    if window_wait > 0:
                        logger.info(
                            f"Rate limit reached for {domain}. "
                            f"Waiting {window_wait:.2f}s..."
                        )
                        time.sleep(window_wait)
                        wait_time += window_wait
                        now = time.time()
            
            # Add this request
            self.redis_client.zadd(requests_key, {str(now): now})
            self.redis_client.expire(requests_key, self.time_window_seconds + 10)
            
            # Update last request time
            self.redis_client.set(
                last_request_key,
                str(now),
                ex=self.time_window_seconds
            )
            
        except Exception as e:
            logger.error(f"Redis rate limiting error: {e}. Falling back to local.")
            return self._wait_if_needed_local(domain)
        
        return wait_time
    
    def reset_domain(self, url: str):
        """Reset rate limit for a specific domain."""
        domain = self._extract_domain(url)
        
        if self.redis_client:
            requests_key = f"rate_limit:requests:{domain}"
            last_request_key = f"rate_limit:last:{domain}"
            self.redis_client.delete(requests_key, last_request_key)
        else:
            with self._lock:
                self._local_requests.pop(domain, None)
                self._local_last_request.pop(domain, None)
        
        logger.info(f"Rate limit reset for domain: {domain}")


class GlobalRateLimiter:
    """
    Global rate limiter to control overall system request rate.
    Prevents the entire system from making too many requests.
    """
    
    def __init__(
        self,
        redis_client: Optional[Redis] = None,
        max_requests_per_minute: int = 60,
        max_concurrent_requests: int = 10
    ):
        """
        Initialize global rate limiter.
        
        Args:
            redis_client: Redis client for distributed limiting
            max_requests_per_minute: Max total requests per minute
            max_concurrent_requests: Max concurrent requests
        """
        self.redis_client = redis_client
        self.max_requests_per_minute = max_requests_per_minute
        self.max_concurrent_requests = max_concurrent_requests
        
        # Local storage
        self._local_requests = []
        self._local_concurrent = 0
        self._lock = Lock()
        
        logger.info(
            f"GlobalRateLimiter initialized: "
            f"{max_requests_per_minute} req/min, "
            f"{max_concurrent_requests} concurrent"
        )
    
    def acquire(self) -> bool:
        """
        Acquire permission to make a request.
        
        Returns:
            True if permission granted
        """
        if self.redis_client:
            return self._acquire_distributed()
        else:
            return self._acquire_local()
    
    def _acquire_local(self) -> bool:
        """Local acquisition logic."""
        with self._lock:
            now = time.time()
            
            # Check concurrent limit
            if self._local_concurrent >= self.max_concurrent_requests:
                logger.warning("Max concurrent requests reached")
                return False
            
            # Clean old requests (older than 1 minute)
            cutoff = now - 60
            self._local_requests = [
                req_time for req_time in self._local_requests
                if req_time > cutoff
            ]
            
            # Check rate limit
            if len(self._local_requests) >= self.max_requests_per_minute:
                logger.warning("Max requests per minute reached")
                return False
            
            # Grant permission
            self._local_requests.append(now)
            self._local_concurrent += 1
            return True
    
    def _acquire_distributed(self) -> bool:
        """Distributed acquisition using Redis."""
        try:
            now = time.time()
            
            # Check concurrent limit
            concurrent_key = "rate_limit:global:concurrent"
            current_concurrent = self.redis_client.get(concurrent_key)
            if current_concurrent and int(current_concurrent) >= self.max_concurrent_requests:
                logger.warning("Max concurrent requests reached (distributed)")
                return False
            
            # Check rate limit
            requests_key = "rate_limit:global:requests"
            cutoff = now - 60
            self.redis_client.zremrangebyscore(requests_key, 0, cutoff)
            
            current_count = self.redis_client.zcard(requests_key)
            if current_count >= self.max_requests_per_minute:
                logger.warning("Max requests per minute reached (distributed)")
                return False
            
            # Grant permission
            self.redis_client.zadd(requests_key, {str(now): now})
            self.redis_client.expire(requests_key, 70)
            self.redis_client.incr(concurrent_key)
            self.redis_client.expire(concurrent_key, 300)
            
            return True
            
        except Exception as e:
            logger.error(f"Redis global rate limiting error: {e}")
            return self._acquire_local()
    
    def release(self):
        """Release a request slot."""
        if self.redis_client:
            self._release_distributed()
        else:
            self._release_local()
    
    def _release_local(self):
        """Local release logic."""
        with self._lock:
            if self._local_concurrent > 0:
                self._local_concurrent -= 1
    
    def _release_distributed(self):
        """Distributed release using Redis."""
        try:
            concurrent_key = "rate_limit:global:concurrent"
            self.redis_client.decr(concurrent_key)
        except Exception as e:
            logger.error(f"Redis release error: {e}")
            self._release_local()


class RateLimitedRequestManager:
    """
    High-level manager that combines domain and global rate limiting.
    """
    
    def __init__(self, redis_url: Optional[str] = None):
        """
        Initialize rate limited request manager.
        
        Args:
            redis_url: Redis connection URL
        """
        # Initialize Redis client if URL provided
        self.redis_client = None
        if redis_url:
            try:
                self.redis_client = Redis.from_url(redis_url, decode_responses=True)
                self.redis_client.ping()
                logger.info("Connected to Redis for distributed rate limiting")
            except Exception as e:
                logger.warning(f"Failed to connect to Redis: {e}. Using local mode.")
                self.redis_client = None
        
        # Initialize rate limiters
        self.domain_limiter = DomainRateLimiter(
            redis_client=self.redis_client,
            max_requests_per_domain=10,
            time_window_seconds=60,
            min_request_interval=2.0
        )
        
        self.global_limiter = GlobalRateLimiter(
            redis_client=self.redis_client,
            max_requests_per_minute=60,
            max_concurrent_requests=10
        )
    
    def wait_and_acquire(self, url: str) -> bool:
        """
        Wait for rate limits and acquire permission to make request.
        
        Args:
            url: URL to request
            
        Returns:
            True if permission granted
        """
        # First check global limit
        max_attempts = 5
        for attempt in range(max_attempts):
            if self.global_limiter.acquire():
                break
            
            if attempt < max_attempts - 1:
                logger.info(f"Global limit reached, waiting... (attempt {attempt + 1})")
                time.sleep(2)
            else:
                logger.error("Failed to acquire global rate limit after max attempts")
                return False
        
        # Then apply domain-specific rate limiting
        try:
            wait_time = self.domain_limiter.wait_if_needed(url)
            if wait_time > 0:
                logger.debug(f"Waited {wait_time:.2f}s for domain rate limit")
            return True
        except Exception as e:
            logger.error(f"Error in domain rate limiting: {e}")
            self.global_limiter.release()
            return False
    
    def release(self):
        """Release the request slot."""
        self.global_limiter.release()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.release()


# Global instance
_rate_limit_manager: Optional[RateLimitedRequestManager] = None


def get_rate_limit_manager() -> RateLimitedRequestManager:
    """Get or create global rate limit manager instance."""
    global _rate_limit_manager
    
    if _rate_limit_manager is None:
        _rate_limit_manager = RateLimitedRequestManager(
            redis_url=settings.REDIS_URL
        )
    
    return _rate_limit_manager
