"""
Simple test script to verify rate limiting functionality.
Run this to test the rate limiting implementation.
"""
import time
import logging
from app.utils.rate_limiter import DomainRateLimiter, GlobalRateLimiter, RateLimitedRequestManager
from app.tasks.priority_manager import TaskThrottleManager, TaskPriority

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_domain_rate_limiter():
    """Test domain-based rate limiting."""
    logger.info("=" * 60)
    logger.info("Testing Domain Rate Limiter")
    logger.info("=" * 60)
    
    # Create limiter with strict limits for testing
    limiter = DomainRateLimiter(
        redis_client=None,  # Use local mode
        max_requests_per_domain=3,
        time_window_seconds=10,
        min_request_interval=1.0
    )
    
    test_url = "https://example.com/page"
    
    logger.info(f"Making 5 requests to {test_url}")
    logger.info("Expected: First 3 should be fast, then delays should occur")
    
    for i in range(5):
        start = time.time()
        wait_time = limiter.wait_if_needed(test_url)
        elapsed = time.time() - start
        
        logger.info(
            f"Request {i+1}: waited {wait_time:.2f}s, "
            f"total elapsed {elapsed:.2f}s"
        )
    
    logger.info("✓ Domain rate limiter test completed\n")


def test_global_rate_limiter():
    """Test global rate limiting."""
    logger.info("=" * 60)
    logger.info("Testing Global Rate Limiter")
    logger.info("=" * 60)
    
    # Create limiter with strict limits
    limiter = GlobalRateLimiter(
        redis_client=None,  # Use local mode
        max_requests_per_minute=5,
        max_concurrent_requests=3
    )
    
    logger.info("Testing concurrent request limits (max 3)")
    
    # Test concurrent limit
    acquired = []
    for i in range(5):
        result = limiter.acquire()
        acquired.append(result)
        logger.info(f"Acquire attempt {i+1}: {'✓ Success' if result else '✗ Blocked'}")
    
    # Release some
    logger.info("\nReleasing 2 requests...")
    limiter.release()
    limiter.release()
    
    # Try to acquire again
    result = limiter.acquire()
    logger.info(f"Acquire after release: {'✓ Success' if result else '✗ Blocked'}")
    
    logger.info("✓ Global rate limiter test completed\n")


def test_rate_limited_request_manager():
    """Test the high-level request manager."""
    logger.info("=" * 60)
    logger.info("Testing Rate Limited Request Manager")
    logger.info("=" * 60)
    
    manager = RateLimitedRequestManager(redis_url=None)
    
    urls = [
        "https://example.com/page1",
        "https://example.com/page2",
        "https://different.com/page1",
        "https://example.com/page3",
    ]
    
    logger.info("Making requests to multiple domains")
    
    for i, url in enumerate(urls):
        start = time.time()
        success = manager.wait_and_acquire(url)
        elapsed = time.time() - start
        
        if success:
            logger.info(
                f"Request {i+1} to {url}: "
                f"✓ Acquired (waited {elapsed:.2f}s)"
            )
            manager.release()
        else:
            logger.info(f"Request {i+1} to {url}: ✗ Failed to acquire")
    
    logger.info("✓ Request manager test completed\n")


def test_task_throttle_manager():
    """Test task throttling."""
    logger.info("=" * 60)
    logger.info("Testing Task Throttle Manager")
    logger.info("=" * 60)
    
    manager = TaskThrottleManager(redis_client=None)
    
    task_name = "scraping_tasks.scrape_google_task"
    
    logger.info(f"Testing throttle for: {task_name}")
    logger.info(f"Limits: {manager.throttle_limits[task_name]}")
    
    # Simulate task starts
    logger.info("\nSimulating 3 concurrent task starts...")
    for i in range(3):
        can_execute = manager.can_execute_task(task_name)
        logger.info(f"Task {i+1} can execute: {can_execute}")
        
        if can_execute:
            manager.record_task_start(task_name)
    
    # Check stats
    stats = manager.get_task_stats(task_name)
    logger.info(f"\nCurrent stats: {stats}")
    
    # Try one more (should be blocked if concurrent limit is 2)
    can_execute = manager.can_execute_task(task_name)
    logger.info(f"Task 4 can execute: {can_execute}")
    
    # End some tasks
    logger.info("\nEnding 2 tasks...")
    manager.record_task_end(task_name)
    manager.record_task_end(task_name)
    
    stats = manager.get_task_stats(task_name)
    logger.info(f"Stats after ending tasks: {stats}")
    
    logger.info("✓ Task throttle manager test completed\n")


def test_task_priorities():
    """Test task priority levels."""
    logger.info("=" * 60)
    logger.info("Testing Task Priorities")
    logger.info("=" * 60)
    
    priorities = [
        ("Export task", TaskPriority.CRITICAL),
        ("Google search", TaskPriority.HIGH),
        ("Website extraction", TaskPriority.NORMAL),
        ("Retry task", TaskPriority.LOW),
        ("Bulk operation", TaskPriority.BULK),
    ]
    
    logger.info("Priority levels (lower number = higher priority):")
    for name, priority in priorities:
        logger.info(f"  {name}: {priority.value} ({priority.name})")
    
    logger.info("✓ Task priorities test completed\n")


def main():
    """Run all tests."""
    logger.info("\n" + "=" * 60)
    logger.info("RATE LIMITING AND REQUEST CONTROL TESTS")
    logger.info("=" * 60 + "\n")
    
    try:
        test_domain_rate_limiter()
        test_global_rate_limiter()
        test_rate_limited_request_manager()
        test_task_throttle_manager()
        test_task_priorities()
        
        logger.info("=" * 60)
        logger.info("ALL TESTS COMPLETED SUCCESSFULLY ✓")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"Test failed with error: {e}", exc_info=True)
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
