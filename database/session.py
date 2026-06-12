import asyncio
import logging
from sqlalchemy import create_engine, text, exc, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool

from config import config
from database.base import Base

logger = logging.getLogger(__name__)

DATABASE_URL = config["database"]["url"]

# ✅ PRODUCTION-READY pool configuration
engine_args = {
    "echo": False,
    "future": True,
    "poolclass": QueuePool,  # 🔥 Use connection pooling
    "pool_size": 5,           # 🔥 Keep 5 connections ready
    "max_overflow": 10,       # 🔥 Allow up to 10 more connections
    "pool_pre_ping": True,    # 🔥 CRITICAL: Test connection before use
    "pool_recycle": 3600,     # 🔥 Recycle connections every hour
    "connect_args": {
        "connect_timeout": 10,  # 🔥 Fail fast if unreachable
        "application_name": "scrapper_spain",
    },
}

# SQLite specific config (for tests)
if DATABASE_URL.startswith("sqlite"):
    engine_args["poolclass"] = None
    engine_args.pop("pool_size", None)
    engine_args.pop("max_overflow", None)
    engine_args.pop("pool_pre_ping", None)
    engine_args.pop("pool_recycle", None)
    engine_args["connect_args"] = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, **engine_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

# 🔥 Log pool events for debugging
@event.listens_for(QueuePool, "connect")
def receive_connect(dbapi_conn, connection_record):
    logger.debug("✅ New DB connection established")

@event.listens_for(QueuePool, "checkin")
def receive_checkin(dbapi_conn, connection_record):
    logger.debug("✅ DB connection returned to pool")


async def wait_for_db(max_retries: int = 30, retry_delay: float = 1.0) -> bool:
    """
    🔥 Wait for PostgreSQL to be ready with exponential backoff.

    Call this at application startup to ensure DB is accessible.
    Uses exponential backoff to handle slow database startup.

    Args:
        max_retries: Max connection attempts (30 ≈ 30-60 sec)
        retry_delay: Initial delay between retries (sec)

    Returns:
        True if successful, raises RuntimeError if failed
    """
    attempt = 0
    current_delay = retry_delay

    while attempt < max_retries:
        try:
            with engine.connect() as connection:
                connection.execute(text("SELECT 1"))
                logger.info(f"✅ Database connection successful (attempt {attempt + 1}/{max_retries})")
                return True

        except exc.OperationalError as e:
            attempt += 1
            if attempt >= max_retries:
                logger.error(
                    f"❌ Database connection failed after {max_retries} attempts. "
                    f"Is PostgreSQL running and accessible at {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else 'config'}?"
                )
                raise RuntimeError(
                    f"Could not connect to database after {max_retries} retries. "
                    f"Error: {str(e)[:100]}"
                ) from e

            logger.warning(
                f"⏳ DB not ready (attempt {attempt}/{max_retries}). "
                f"Retrying in {current_delay:.1f}s..."
            )
            await asyncio.sleep(current_delay)
            current_delay = min(current_delay * 1.1, 10.0)  # Cap at 10s, 10% increase

        except Exception as e:
            logger.error(f"❌ Unexpected database error: {e}")
            raise


def init_db():
    """
    Initialize database tables.

    ⚠️  Call wait_for_db() BEFORE this in run_scrapper.py!
    """
    try:
        from models import Result
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Database tables initialized")
    except Exception as e:
        logger.error(f"❌ Failed to initialize database: {e}")
        raise


def close_db():
    """Close all database connections."""
    try:
        engine.dispose()
        logger.info("🔗 Database connections closed")
    except Exception as e:
        logger.error(f"❌ Error closing database: {e}")