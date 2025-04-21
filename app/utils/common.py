import logging
import os
import time
from datetime import datetime

# Configure logging
def setup_logging():
    """Set up logging configuration"""
    log_dir = "logs"
    
    # Create logs directory if it doesn't exist
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # Create log file with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(log_dir, f"kyagent_{timestamp}.log")
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    
    return logging.getLogger("KyAgent")

# Timing decorator
def timing_decorator(func):
    """Decorator to measure function execution time"""
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        
        logger = logging.getLogger("KyAgent")
        logger.info(f"Function {func.__name__} took {end_time - start_time:.2f} seconds to execute")
        
        return result
    return wrapper

# Format currency
def format_currency(amount):
    """Format currency with commas"""
    return f"¥{amount:,.2f}"

# Format percentage
def format_percentage(value):
    """Format value as percentage"""
    return f"{value:.2f}%"

# Format date
def format_date(date_str):
    """Format date string to standard format"""
    try:
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        return date_obj.strftime("%Y年%m月%d日")
    except ValueError:
        return date_str 