"""Database connection and session management"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from core.config import settings
import logging

logger = logging.getLogger(__name__)

# Base class for models
Base = declarative_base()

# Import all models to ensure they're registered with Base.metadata
# This must happen after Base is defined but before init_db is called
def _import_models():
    """Import all models to register them with SQLAlchemy metadata"""
    try:
        # Import all model modules
        from models import database  # Main models
        from models.db import (  # Resume upload models
            Resume, Candidate, Education, WorkExperience,
            Skill, Certification, DuplicateCheck
        )
        logger.info("All models imported successfully")
    except ImportError as e:
        logger.warning(f"Some models could not be imported: {e}")

# Import models on module load
_import_models()

# Lazy initialization - will be created on first access
_engine = None
_async_session_local = None


def get_engine():
    """Get or create the async engine (lazy initialization)"""
    global _engine
    if _engine is None:
        logger.info(f"Creating async engine with URL: {settings.database_url}")
        
        # Configure connect_args based on database type
        connect_args = {}
        pool_size = 20
        max_overflow = 40
        
        if "sqlite" in settings.database_url.lower():
            # SQLite-specific optimizations for concurrent access
            connect_args = {
                "check_same_thread": False,
                "timeout": 30.0,  # Increase timeout for write locks
            }
            # SQLite doesn't support large connection pools
            pool_size = 5
            max_overflow = 10
            
            logger.info("🔧 SQLite detected - enabling WAL mode and connection pooling optimizations")
        
        _engine = create_async_engine(
            settings.database_url,
            echo=settings.debug,
            pool_pre_ping=True,
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_timeout=30,
            pool_recycle=3600,  # Recycle connections after 1 hour
            future=True,
            connect_args=connect_args
        )
        
        # Enable WAL mode for SQLite to allow concurrent reads during writes
        if "sqlite" in settings.database_url.lower():
            import asyncio
            asyncio.create_task(_enable_wal_mode(_engine))
    
    return _engine


async def _enable_wal_mode(engine):
    """Enable WAL (Write-Ahead Logging) mode for SQLite to improve concurrency"""
    try:
        async with engine.begin() as conn:
            await conn.execute("PRAGMA journal_mode=WAL;")
            await conn.execute("PRAGMA synchronous=NORMAL;")
            await conn.execute("PRAGMA busy_timeout=30000;")  # 30 seconds
            await conn.execute("PRAGMA cache_size=-64000;")  # 64MB cache
            logger.info("✅ SQLite WAL mode enabled - concurrent reads/writes now supported")
    except Exception as e:
        logger.warning(f"⚠️ Could not enable WAL mode: {e}")


def get_async_session():
    """Get or create the session factory (lazy initialization)"""
    global _async_session_local
    if _async_session_local is None:
        _async_session_local = async_sessionmaker(
            get_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
            autocommit=False
        )
    return _async_session_local


# Create module-level references (these trigger lazy init when accessed)
engine = get_engine()
AsyncSessionLocal = get_async_session()

# Synchronous session for Celery tasks and other sync contexts
# Note: This uses the sync SQLite driver, not aiosqlite
def get_sync_session():
    """Get or create a synchronous session factory for Celery tasks"""
    from sqlalchemy import create_engine as create_sync_engine
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy import event
    
    # Convert async URL to sync URL
    sync_url = settings.database_url.replace('+aiosqlite', '').replace('+asyncpg', '')
    
    # Configure connect_args based on database type
    connect_args = {}
    pool_size = 20
    max_overflow = 40
    
    if "sqlite" in sync_url.lower():
        connect_args = {
            "check_same_thread": False,
            "timeout": 30.0
        }
        pool_size = 5
        max_overflow = 10
    
    sync_engine = create_sync_engine(
        sync_url,
        echo=settings.debug,
        pool_size=pool_size,
        max_overflow=max_overflow,
        pool_timeout=30,
        pool_recycle=3600,
        connect_args=connect_args
    )
    
    # Enable WAL mode for SQLite sync engine
    if "sqlite" in sync_url.lower():
        @event.listens_for(sync_engine, "connect")
        def set_sqlite_pragma(dbapi_conn, connection_record):
            cursor = dbapi_conn.cursor()
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA synchronous=NORMAL")
            cursor.execute("PRAGMA busy_timeout=30000")
            cursor.execute("PRAGMA cache_size=-64000")
            cursor.close()
    
    return sessionmaker(autocommit=False, autoflush=False, bind=sync_engine)

# Create sync session maker for Celery tasks
SessionLocal = get_sync_session()


async def get_db():
    """Dependency for getting database session"""
    session_maker = get_async_session()
    async with session_maker() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    """Initialize database tables"""
    eng = get_engine()
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created successfully")


async def close_db():
    """Close database connections"""
    eng = get_engine()
    await eng.dispose()
    logger.info("Database connections closed")
