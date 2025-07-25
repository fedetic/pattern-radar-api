#!/usr/bin/env python3
"""
Simple database setup script for pattern analysis application
Run this after ensuring PostgreSQL is running and database is created
"""

import sys
import os
from pathlib import Path

# Add current directory to path for imports
sys.path.append(str(Path(__file__).parent))

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("Loaded environment variables from .env file")
except ImportError:
    print("Warning: python-dotenv not available")

def check_environment():
    """Check if environment is ready for database setup"""
    print("Checking environment...")
    
    # Check DATABASE_URL
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        print("ERROR: DATABASE_URL environment variable not found")
        print("Please set DATABASE_URL in your .env file or environment")
        return False
    
    print(f"OK: DATABASE_URL found: {db_url.split('@')[1] if '@' in db_url else 'hidden'}")
    
    # Check if required packages are available
    try:
        import sqlalchemy
        import psycopg2
        print("OK: Required packages available")
    except ImportError as e:
        print(f"ERROR: Missing required package: {e}")
        print("Please run: pip install -r requirements.txt")
        return False
    
    return True

def setup_database():
    """Set up the database with tables and seed data"""
    print("\nSetting up database...")
    
    try:
        # Import and run database initialization
        from database.init_db import init_database_full
        
        success = init_database_full()
        
        if success:
            print("OK: Database setup completed successfully!")
            return True
        else:
            print("ERROR: Database setup failed!")
            return False
            
    except Exception as e:
        print(f"ERROR: Error during database setup: {e}")
        return False

def test_database():
    """Test database functionality"""
    print("\nTesting database functionality...")
    
    try:
        from database.connection import get_database_manager
        from database.repositories.trading_pairs_repository import TradingPairsRepository
        from database.repositories.pattern_types_repository import PatternTypesRepository
        
        db_manager = get_database_manager()
        
        # Test connection
        if not db_manager.test_connection():
            print("ERROR: Database connection test failed")
            return False
        
        print("OK: Database connection test passed")
        
        # Test table counts
        with db_manager.get_db_session() as session:
            pairs_repo = TradingPairsRepository(session)
            patterns_repo = PatternTypesRepository(session)
            
            pairs_count = pairs_repo.count()
            patterns_count = patterns_repo.count()
            
            print(f"OK: Trading pairs table: {pairs_count} records")
            print(f"OK: Pattern types table: {patterns_count} records")
            
            if patterns_count == 0:
                print("WARNING: No pattern types found. Database may not be seeded properly.")
            
        return True
        
    except Exception as e:
        print(f"ERROR: Database test failed: {e}")
        return False

def main():
    """Main setup function"""
    print("=" * 60)
    print("Pattern Analysis Database Setup")
    print("=" * 60)
    
    # Check environment
    if not check_environment():
        print("\nERROR: Environment check failed. Please fix the issues above.")
        return False
    
    # Setup database
    if not setup_database():
        print("\nERROR: Database setup failed. Please check the errors above.")
        return False
    
    # Test database
    if not test_database():
        print("\nERROR: Database test failed. Please check the errors above.")
        return False
    
    print("\n" + "=" * 60)
    print("SUCCESS: Database setup completed successfully!")
    print("=" * 60)
    print("\nYou can now:")
    print("1. Start the FastAPI server: uvicorn main:app --reload")
    print("2. Check database stats: GET http://localhost:8000/db/stats")
    print("3. Sync trading pairs: POST http://localhost:8000/db/sync-pairs")
    print("4. View API docs: http://localhost:8000/docs")
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\nSetup cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        sys.exit(1)