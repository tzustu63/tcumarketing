"""
Utility functions package.
"""

from app.utils.logging_utils import (
    log_scraping_to_db,
    log_scraping_success,
    log_scraping_error,
    get_error_logs,
    get_task_logs,
    count_error_logs
)

__all__ = [
    "log_scraping_to_db",
    "log_scraping_success",
    "log_scraping_error",
    "get_error_logs",
    "get_task_logs",
    "count_error_logs"
]
