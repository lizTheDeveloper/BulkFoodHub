"""
Database connection and session management for BulkFoodHub.
Handles PostgreSQL database connections and Redis caching.
"""

from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
import redis
from typing import Generator
import contextlib

from app.core.config import get_database_url, get_redis_url, settings
from app.core.logging import get_logger, log_database_operation

logger = get_logger(__name__)

# Database engine configuration
engine = create_engine(
    get_database_url(),
    poolclass=StaticPool if settings.is_testing else None,
    pool_pre_ping=True,
    pool_recycle=300,
    echo=settings.debug,
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()

# Metadata for migrations
metadata = MetaData()

# Redis connection
redis_client = None


def get_redis_client() -> redis.Redis:
    """Get Redis client instance."""
    global redis_client
    if redis_client is None:
        try:
            redis_client = redis.from_url(
                get_redis_url(),
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
            )
            # Test connection
            redis_client.ping()
            logger.info("Redis connection established")
        except Exception as e:
            logger.error("Failed to connect to Redis", error=str(e))
            raise
    return redis_client


def get_db() -> Generator[Session, None, None]:
    """
    Dependency to get database session.
    Yields a database session and ensures it's closed after use.
    """
    db = SessionLocal()
    try:
        log_database_operation("session_start", "database")
        yield db
    except Exception as e:
        log_database_operation("session_error", "database", error=str(e))
        db.rollback()
        raise
    finally:
        log_database_operation("session_end", "database")
        db.close()


@contextlib.contextmanager
def get_db_context():
    """
    Context manager for database sessions.
    Use this for non-FastAPI contexts where dependency injection isn't available.
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception as e:
        db.rollback()
        raise
    finally:
        db.close()


def init_db() -> None:
    """Initialize database tables."""
    try:
        log_database_operation("init_database", "database")
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        log_database_operation("init_database_error", "database", error=str(e))
        logger.error("Failed to initialize database", error=str(e))
        raise


def test_db_connection() -> bool:
    """Test database connection."""
    try:
        with get_db_context() as db:
            from sqlalchemy import text
            db.execute(text("SELECT 1"))
        logger.info("Database connection test successful")
        return True
    except Exception as e:
        logger.error("Database connection test failed", error=str(e))
        return False


def test_redis_connection() -> bool:
    """Test Redis connection."""
    try:
        client = get_redis_client()
        client.ping()
        logger.info("Redis connection test successful")
        return True
    except Exception as e:
        logger.error("Redis connection test failed", error=str(e))
        return False


class DatabaseManager:
    """Database manager for handling connections and operations."""
    
    def __init__(self):
        self.engine = engine
        self.session_factory = SessionLocal
        self.redis_client = None
    
    def get_session(self) -> Session:
        """Get a new database session."""
        return self.session_factory()
    
    def get_redis(self) -> redis.Redis:
        """Get Redis client."""
        if self.redis_client is None:
            self.redis_client = get_redis_client()
        return self.redis_client
    
    def health_check(self) -> dict:
        """Perform health check on database and Redis."""
        db_status = test_db_connection()
        redis_status = test_redis_connection()
        
        return {
            "database": "healthy" if db_status else "unhealthy",
            "redis": "healthy" if redis_status else "unhealthy",
            "overall": "healthy" if db_status and redis_status else "unhealthy"
        }


# Global database manager instance
db_manager = DatabaseManager()
