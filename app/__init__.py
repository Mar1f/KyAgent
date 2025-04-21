# app/__init__.py
from app.utils.common import setup_logging

# Setup logging
logger = setup_logging()
logger.info("Initializing KyAgent - 考研信息查询系统") 