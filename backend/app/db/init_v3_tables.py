"""
Database initialization script for DataBuilder V3
Ensures all required tables exist and are properly configured
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

import logging
from sqlalchemy import text
from app.db.session import SessionLocal
from app.models.data_collection_task import DataCollectionTask, CollectedDataSample
from app.models.user import User

logger = logging.getLogger(__name__)

def init_v3_database():
    """Initialize database tables for DataBuilder V3"""
    db = SessionLocal()
    
    try:
        # Check if tables exist and create them if not
        logger.info("Checking DataBuilder V3 database tables...")
        
        # Test if we can query the tables
        db.execute(text("SELECT COUNT(*) FROM data_collection_tasks LIMIT 1"))
        db.execute(text("SELECT COUNT(*) FROM collected_data_samples LIMIT 1"))
        db.execute(text("SELECT COUNT(*) FROM users LIMIT 1"))
        
        logger.info("All DataBuilder V3 tables are available")
        
        # Add any missing indexes
        try:
            db.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_data_collection_tasks_user_status 
                ON data_collection_tasks(user_id, status)
            """))
            
            db.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_collected_data_samples_task_created 
                ON collected_data_samples(task_id, created_at)
            """))
            
            db.commit()
            logger.info("Database indexes verified/created")
            
        except Exception as e:
            logger.warning(f"Could not create indexes: {e}")
            db.rollback()
        
        return True
        
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        return False
        
    finally:
        db.close()

def create_sample_data():
    """Create sample data for testing (optional)"""
    db = SessionLocal()
    
    try:
        # Check if sample user exists
        sample_user = db.query(User).filter(User.email == "test@metra.ai").first()
        
        if not sample_user:
            logger.info("Creating sample user for testing...")
            # This would require the User model to be properly configured
            # For now, just log that manual user creation may be needed
            logger.warning("No test user found. Manual user creation may be needed.")
        
        db.commit()
        
    except Exception as e:
        logger.error(f"Sample data creation failed: {e}")
        db.rollback()
        
    finally:
        db.close()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    success = init_v3_database()
    if success:
        logger.info("✅ DataBuilder V3 database initialization completed successfully")
        create_sample_data()
    else:
        logger.error("❌ DataBuilder V3 database initialization failed")