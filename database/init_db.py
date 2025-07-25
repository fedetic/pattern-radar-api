"""
Database initialization script
Sets up tables and seeds initial data
"""

import os
import sys
from pathlib import Path

# Add the parent directory to sys.path so we can import from the main package
sys.path.append(str(Path(__file__).parent.parent))

from database.connection import get_database_manager, init_database
from database.models import Base
from database.repositories.pattern_types_repository import PatternTypesRepository
from database.seed_data import get_pattern_types_seed_data
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def execute_schema_file():
    """Execute the schema SQL file to create tables and indexes"""
    try:
        db_manager = get_database_manager()
        schema_file_path = Path(__file__).parent / 'schema.sql'
        
        if schema_file_path.exists():
            db_manager.execute_schema_file(str(schema_file_path))
            logger.info("Schema file executed successfully")
        else:
            logger.warning(f"Schema file not found at {schema_file_path}")
            
    except Exception as e:
        logger.error(f"Error executing schema file: {e}")
        raise

def seed_pattern_types():
    """Seed the pattern types table with initial data"""
    try:
        db_manager = get_database_manager()
        
        with db_manager.get_db_session() as session:
            pattern_repo = PatternTypesRepository(session)
            
            # Get seed data
            patterns_data = get_pattern_types_seed_data()
            
            # Check if patterns already exist
            existing_count = pattern_repo.count()
            if existing_count > 0:
                logger.info(f"Pattern types table already has {existing_count} records. Skipping seed.")
                return existing_count
                
            # Insert pattern types
            inserted_count = pattern_repo.bulk_insert_pattern_types(patterns_data)
            logger.info(f"Seeded {inserted_count} pattern types")
            
            return inserted_count
            
    except Exception as e:
        logger.error(f"Error seeding pattern types: {e}")
        raise

def verify_database_setup():
    """Verify that the database is set up correctly"""
    try:
        db_manager = get_database_manager()
        
        # Test connection
        if not db_manager.test_connection():
            raise Exception("Database connection test failed")
            
        # Get database info
        db_info = db_manager.get_db_info()
        logger.info(f"Database info: {db_info}")
        
        # Check table counts
        with db_manager.get_db_session() as session:
            from database.repositories.trading_pairs_repository import TradingPairsRepository
            from database.repositories.pattern_types_repository import PatternTypesRepository
            from database.repositories.ohlcv_repository import OHLCVRepository
            from database.repositories.detected_patterns_repository import DetectedPatternsRepository
            
            pairs_repo = TradingPairsRepository(session)
            patterns_repo = PatternTypesRepository(session)
            ohlcv_repo = OHLCVRepository(session)
            detected_repo = DetectedPatternsRepository(session)
            
            logger.info(f"Table counts:")
            logger.info(f"  - Trading pairs: {pairs_repo.count()}")
            logger.info(f"  - Pattern types: {patterns_repo.count()}")
            logger.info(f"  - OHLCV data: {ohlcv_repo.count()}")
            logger.info(f"  - Detected patterns: {detected_repo.count()}")
        
        return True
        
    except Exception as e:
        logger.error(f"Database verification failed: {e}")
        return False

def init_database_full():
    """Complete database initialization"""
    try:
        logger.info("Starting database initialization...")
        
        # Initialize database connection and create engine
        db_manager = init_database()
        logger.info("Database manager initialized")
        
        # Execute schema file to create tables and indexes
        execute_schema_file()
        logger.info("Database schema created")
        
        # Seed pattern types
        pattern_count = seed_pattern_types()
        logger.info(f"Pattern types seeded: {pattern_count}")
        
        # Verify setup
        if verify_database_setup():
            logger.info("Database initialization completed successfully!")
            return True
        else:
            logger.error("Database initialization verification failed")
            return False
            
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        return False

def reset_database():
    """Reset the database by dropping and recreating all tables"""
    try:
        logger.warning("Resetting database - all data will be lost!")
        
        db_manager = get_database_manager()
        
        # Drop all tables
        Base.metadata.drop_all(bind=db_manager.engine)
        logger.info("All tables dropped")
        
        # Recreate tables
        Base.metadata.create_all(bind=db_manager.engine)
        logger.info("All tables recreated")
        
        # Re-execute schema file for views and functions
        execute_schema_file()
        logger.info("Schema file re-executed")
        
        # Re-seed data
        pattern_count = seed_pattern_types()
        logger.info(f"Pattern types re-seeded: {pattern_count}")
        
        return verify_database_setup()
        
    except Exception as e:
        logger.error(f"Database reset failed: {e}")
        return False

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Database initialization script")
    parser.add_argument("--reset", action="store_true", help="Reset the database (drops all tables)")
    parser.add_argument("--verify", action="store_true", help="Only verify database setup")
    parser.add_argument("--seed-only", action="store_true", help="Only seed pattern types")
    
    args = parser.parse_args()
    
    try:
        if args.reset:
            success = reset_database()
        elif args.verify:
            success = verify_database_setup()
        elif args.seed_only:
            success = seed_pattern_types() > 0
        else:
            success = init_database_full()
        
        if success:
            logger.info("Operation completed successfully!")
            sys.exit(0)
        else:
            logger.error("Operation failed!")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)