from app.storage.database import engine
from app.storage.models import Base
from app.core.logger import logger

logger.info("Creating database tables...")

Base.metadata.create_all(bind=engine)

logger.info("Database tables created successfully.")