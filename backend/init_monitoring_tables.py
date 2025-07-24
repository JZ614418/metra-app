#!/usr/bin/env python3
"""
Monitoring Tables Initialization Script
监控表初始化脚本 - 创建生产级监控所需的数据库表
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import logging
from sqlalchemy import create_engine, text
from app.db.session import SessionLocal, engine
from app.models.monitoring import (
    APICallLog, DeploymentMetrics, UsageStatistics, 
    SystemMetrics, AlertEvent, ModelPerformanceMetrics
)
from app.db.base_class import Base

logger = logging.getLogger(__name__)

def create_monitoring_tables():
    """Create all monitoring-related database tables"""
    try:
        logger.info("🔄 Creating monitoring database tables...")
        
        # Create all monitoring tables
        Base.metadata.create_all(bind=engine, tables=[
            APICallLog.__table__,
            DeploymentMetrics.__table__,
            UsageStatistics.__table__,
            SystemMetrics.__table__,
            AlertEvent.__table__,
            ModelPerformanceMetrics.__table__
        ])
        
        logger.info("✅ Monitoring tables created successfully")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to create monitoring tables: {e}")
        return False

def create_monitoring_indexes():
    """Create indexes for better monitoring performance"""
    db = SessionLocal()
    
    try:
        logger.info("🔄 Creating monitoring table indexes...")
        
        # API Call Logs indexes
        db.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_api_calls_deployment_time 
            ON api_call_logs(deployment_id, timestamp)
        """))
        
        db.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_api_calls_user_time 
            ON api_call_logs(user_id, timestamp)
        """))
        
        db.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_api_calls_status_time 
            ON api_call_logs(status_code, timestamp)
        """))
        
        # Deployment Metrics indexes
        db.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_deployment_metrics_id_time 
            ON deployment_metrics(deployment_id, date)
        """))
        
        # System Metrics indexes
        db.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_system_metrics_time 
            ON system_metrics(timestamp)
        """))
        
        # Alert Events indexes
        db.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_alerts_status_severity 
            ON alert_events(status, severity)
        """))
        
        db.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_alerts_triggered_time 
            ON alert_events(triggered_at)
        """))
        
        # Usage Statistics indexes
        db.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_usage_stats_user_date 
            ON usage_statistics(user_id, date)
        """))
        
        db.commit()
        logger.info("✅ Monitoring indexes created successfully")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to create monitoring indexes: {e}")
        db.rollback()
        return False
        
    finally:
        db.close()

def verify_monitoring_tables():
    """Verify that all monitoring tables exist and are accessible"""
    db = SessionLocal()
    
    try:
        logger.info("🔍 Verifying monitoring tables...")
        
        # Test each table
        tables_to_test = [
            ("api_call_logs", "API Call Logs"),
            ("deployment_metrics", "Deployment Metrics"),  
            ("usage_statistics", "Usage Statistics"),
            ("system_metrics", "System Metrics"),
            ("alert_events", "Alert Events"),
            ("model_performance_metrics", "Model Performance Metrics")
        ]
        
        for table_name, display_name in tables_to_test:
            try:
                result = db.execute(text(f"SELECT COUNT(*) FROM {table_name} LIMIT 1"))
                logger.info(f"  ✅ {display_name} table: OK")
            except Exception as e:
                logger.error(f"  ❌ {display_name} table: FAILED - {e}")
                return False
        
        logger.info("✅ All monitoring tables verified successfully")
        return True
        
    except Exception as e:
        logger.error(f"❌ Monitoring table verification failed: {e}")
        return False
        
    finally:
        db.close()

def main():
    """Main initialization function"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    logger.info("🚀 Starting monitoring database initialization...")
    
    # Step 1: Create tables
    if not create_monitoring_tables():
        logger.error("❌ Failed to create monitoring tables. Exiting.")
        return False
    
    # Step 2: Create indexes
    if not create_monitoring_indexes():
        logger.warning("⚠️ Failed to create some indexes, but continuing...")
    
    # Step 3: Verify tables
    if not verify_monitoring_tables():
        logger.error("❌ Failed to verify monitoring tables. Check your database.")
        return False
    
    logger.info("🎉 Monitoring database initialization completed successfully!")
    logger.info("📊 Your Metra system now has production-grade monitoring capabilities.")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)