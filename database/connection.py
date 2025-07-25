import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from sqlalchemy.exc import SQLAlchemyError
from contextlib import contextmanager
from typing import Generator
import logging

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from .models import Base

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseManager:
    """Database connection and session management"""
    
    def __init__(self):
        self.database_url = os.getenv('DATABASE_URL')
        if not self.database_url:
            raise ValueError("DATABASE_URL environment variable is required")
        
        # Create engine with connection pooling
        self.engine = create_engine(
            self.database_url,
            poolclass=QueuePool,
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True,  # Validate connections before use
            pool_recycle=3600,   # Recycle connections after 1 hour
            echo=False  # Set to True for SQL query logging in development
        )
        
        # Create session factory
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )
        
        # Initialize database
        self._initialize_database()
    
    def _initialize_database(self):
        """Initialize database schema and tables"""
        try:
            # Test connection
            with self.engine.connect() as connection:
                logger.info("Database connection established successfully")
                
                # Create schema if it doesn't exist
                connection.execute(text("CREATE SCHEMA IF NOT EXISTS patternapp"))
                connection.commit()
                logger.info("Schema 'patternapp' ensured to exist")
            
            # Create all tables
            Base.metadata.create_all(bind=self.engine)
            logger.info("Database tables created/verified successfully")
            
        except SQLAlchemyError as e:
            logger.error(f"Database initialization failed: {e}")
            raise
    
    def get_session(self) -> Session:
        """Get a new database session"""
        return self.SessionLocal()
    
    @contextmanager
    def get_db_session(self) -> Generator[Session, None, None]:
        """Context manager for database sessions with automatic cleanup"""
        session = self.get_session()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            session.close()
    
    def execute_schema_file(self, schema_file_path: str):
        """Execute SQL schema file"""
        try:
            with open(schema_file_path, 'r') as file:
                schema_sql = file.read()
            
            with self.engine.connect() as connection:
                # Execute the entire file as one block to handle functions properly
                connection.execute(text(schema_sql))
                connection.commit()
                logger.info(f"Schema file {schema_file_path} executed successfully")
                
        except Exception as e:
            logger.error(f"Error executing schema file {schema_file_path}: {e}")
            raise
    
    def test_connection(self) -> bool:
        """Test database connectivity"""
        try:
            with self.engine.connect() as connection:
                result = connection.execute(text("SELECT 1"))
                return result.fetchone()[0] == 1
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            return False
    
    def get_db_info(self) -> dict:
        """Get database information"""
        try:
            with self.engine.connect() as connection:
                version_result = connection.execute(text("SELECT version()"))
                version = version_result.fetchone()[0]
                
                schema_result = connection.execute(text("""
                    SELECT schema_name 
                    FROM information_schema.schemata 
                    WHERE schema_name = 'patternapp'
                """))
                schema_exists = schema_result.fetchone() is not None
                
                table_result = connection.execute(text("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'patternapp'
                """))
                tables = [row[0] for row in table_result.fetchall()]
                
                return {
                    'version': version,
                    'schema_exists': schema_exists,
                    'tables': tables,
                    'connection_url': self.database_url.split('@')[1] if '@' in self.database_url else 'hidden'
                }
        except Exception as e:
            logger.error(f"Error getting database info: {e}")
            return {'error': str(e)}
    
    def close(self):
        """Close database engine"""
        if hasattr(self, 'engine'):
            self.engine.dispose()
            logger.info("Database engine disposed")

# Global database manager instance
db_manager = None

def get_database_manager() -> DatabaseManager:
    """Get or create the global database manager instance"""
    global db_manager
    if db_manager is None:
        db_manager = DatabaseManager()
    return db_manager

def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency for database sessions"""
    db_mgr = get_database_manager()
    with db_mgr.get_db_session() as session:
        yield session

def init_database():
    """Initialize database - called at application startup"""
    try:
        db_mgr = get_database_manager()
        logger.info("Database initialized successfully")
        return db_mgr
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise

# Utility functions for database operations
def execute_raw_sql(sql: str, params: dict = None) -> list:
    """Execute raw SQL query and return results"""
    db_mgr = get_database_manager()
    try:
        with db_mgr.get_db_session() as session:
            result = session.execute(text(sql), params or {})
            if result.returns_rows:
                return [dict(row._mapping) for row in result.fetchall()]
            else:
                return []
    except Exception as e:
        logger.error(f"Error executing raw SQL: {e}")
        raise

def get_table_stats() -> dict:
    """Get statistics about all tables"""
    stats_sql = """
    SELECT 
        schemaname,
        tablename,
        n_tup_ins as inserts,
        n_tup_upd as updates,
        n_tup_del as deletes,
        n_live_tup as live_tuples,
        n_dead_tup as dead_tuples
    FROM pg_stat_user_tables 
    WHERE schemaname = 'patternapp'
    ORDER BY tablename;
    """
    
    try:
        return execute_raw_sql(stats_sql)
    except Exception as e:
        logger.error(f"Error getting table stats: {e}")
        return []