"""
Anti-detection measures for web scraping.
Includes user-agent rotation, request delays, and retry logic.
"""
import random
import time
import logging
from typing import Callable, Any, Optional
from functools import wraps

logger = logging.getLogger(__name__)


# List of realistic user agents for rotation
USER_AGENTS = [
    # Chrome on Windows
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
    
    # Chrome on macOS
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    
    # Firefox on Windows
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0',
    
    # Firefox on macOS
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0',
    
    # Safari on macOS
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15',
    
    # Edge on Windows
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0',
]


class UserAgentRotator:
    """Manages user agent rotation for anti-detection."""
    
    def __init__(self, user_agents: Optional[list] = None):
        """
        Initialize user agent rotator.
        
        Args:
            user_agents: Optional list of user agents. Uses default if None.
        """
        self.user_agents = user_agents or USER_AGENTS
        self.current_index = 0
    
    def get_random(self) -> str:
        """Get a random user agent."""
        return random.choice(self.user_agents)
    
    def get_next(self) -> str:
        """Get the next user agent in rotation."""
        user_agent = self.user_agents[self.current_index]
        self.current_index = (self.current_index + 1) % len(self.user_agents)
        return user_agent


class RequestDelayer:
    """Manages request delays to avoid rate limiting."""
    
    def __init__(self, min_delay: float = 2.0, max_delay: float = 5.0):
        """
        Initialize request delayer.
        
        Args:
            min_delay: Minimum delay in seconds
            max_delay: Maximum delay in seconds
        """
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.last_request_time = 0
    
    def wait(self):
        """Wait for a random delay between min and max delay."""
        delay = random.uniform(self.min_delay, self.max_delay)
        
        # Ensure minimum time has passed since last request
        elapsed = time.time() - self.last_request_time
        if elapsed < delay:
            time.sleep(delay - elapsed)
        
        self.last_request_time = time.time()
        logger.debug(f"Delayed request by {delay:.2f} seconds")
    
    def set_delay_range(self, min_delay: float, max_delay: float):
        """Update delay range."""
        self.min_delay = min_delay
        self.max_delay = max_delay


def exponential_backoff_retry(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exceptions: tuple = (Exception,)
):
    """
    Decorator for implementing exponential backoff retry logic.
    
    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Base delay in seconds (will be multiplied exponentially)
        max_delay: Maximum delay between retries
        exceptions: Tuple of exception types to catch and retry
        
    Returns:
        Decorated function with retry logic
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                    
                except exceptions as e:
                    last_exception = e
                    
                    if attempt == max_retries:
                        logger.error(
                            f"Function {func.__name__} failed after {max_retries} retries: {e}"
                        )
                        raise
                    
                    # Calculate delay with exponential backoff
                    delay = min(base_delay * (2 ** attempt), max_delay)
                    
                    # Add jitter to avoid thundering herd
                    jitter = random.uniform(0, delay * 0.1)
                    total_delay = delay + jitter
                    
                    logger.warning(
                        f"Attempt {attempt + 1}/{max_retries} failed for {func.__name__}: {e}. "
                        f"Retrying in {total_delay:.2f} seconds..."
                    )
                    
                    time.sleep(total_delay)
            
            # This should never be reached, but just in case
            if last_exception:
                raise last_exception
                
        return wrapper
    return decorator


class RateLimiter:
    """
    Rate limiter to control request frequency.
    """
    
    def __init__(self, max_requests: int = 10, time_window: float = 60.0):
        """
        Initialize rate limiter.
        
        Args:
            max_requests: Maximum number of requests allowed in time window
            time_window: Time window in seconds
        """
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = []
    
    def wait_if_needed(self):
        """Wait if rate limit would be exceeded."""
        now = time.time()
        
        # Remove old requests outside the time window
        self.requests = [req_time for req_time in self.requests 
                        if now - req_time < self.time_window]
        
        # Check if we've hit the limit
        if len(self.requests) >= self.max_requests:
            # Calculate how long to wait
            oldest_request = min(self.requests)
            wait_time = self.time_window - (now - oldest_request)
            
            if wait_time > 0:
                logger.info(f"Rate limit reached. Waiting {wait_time:.2f} seconds...")
                time.sleep(wait_time)
                
                # Clean up again after waiting
                now = time.time()
                self.requests = [req_time for req_time in self.requests 
                               if now - req_time < self.time_window]
        
        # Record this request
        self.requests.append(now)
    
    def reset(self):
        """Reset the rate limiter."""
        self.requests = []


class AntiDetectionManager:
    """
    Manages all anti-detection measures in one place.
    """
    
    def __init__(
        self,
        min_delay: float = 2.0,
        max_delay: float = 5.0,
        max_retries: int = 3,
        rate_limit_requests: int = 10,
        rate_limit_window: float = 60.0
    ):
        """
        Initialize anti-detection manager.
        
        Args:
            min_delay: Minimum delay between requests
            max_delay: Maximum delay between requests
            max_retries: Maximum retry attempts
            rate_limit_requests: Max requests per time window
            rate_limit_window: Time window for rate limiting
        """
        self.user_agent_rotator = UserAgentRotator()
        self.request_delayer = RequestDelayer(min_delay, max_delay)
        self.rate_limiter = RateLimiter(rate_limit_requests, rate_limit_window)
        self.max_retries = max_retries
    
    def get_user_agent(self) -> str:
        """Get a random user agent."""
        return self.user_agent_rotator.get_random()
    
    def wait_before_request(self):
        """Execute all pre-request delays and checks."""
        self.rate_limiter.wait_if_needed()
        self.request_delayer.wait()
    
    def execute_with_retry(
        self,
        func: Callable,
        *args,
        exceptions: tuple = (Exception,),
        **kwargs
    ) -> Any:
        """
        Execute a function with retry logic.
        
        Args:
            func: Function to execute
            *args: Positional arguments for the function
            exceptions: Tuple of exceptions to catch and retry
            **kwargs: Keyword arguments for the function
            
        Returns:
            Result of the function
        """
        retry_decorator = exponential_backoff_retry(
            max_retries=self.max_retries,
            exceptions=exceptions
        )
        wrapped_func = retry_decorator(func)
        return wrapped_func(*args, **kwargs)
