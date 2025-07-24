"""
Database Manager - 统一的数据库管理器
支持SQLite和Supabase的智能切换
"""

import os
import sqlite3
import logging
from typing import Optional, Dict, Any, List
from sqlalchemy import create_engine, MetaData, Table, Column, String, Integer, DateTime, Text, Boolean, JSON, inspect
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import asyncio

from app.core.config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

Base = declarative_base()

class DatabaseManager:
    """统一的数据库管理器"""
    
    def __init__(self):
        self.engine = None
        self.SessionLocal = None
        self.supabase_client = None
        self.is_supabase = False
        self.is_initialized = False
        
    async def initialize(self):
        """初始化数据库连接"""
        try:
            # 首先尝试Supabase
            if await self._try_supabase_connection():
                logger.info("✅ Using Supabase database")
                self.is_supabase = True
                await self._initialize_supabase_tables()
            else:
                # 降级到SQLite
                logger.info("⚠️ Supabase unavailable, using SQLite")
                self.is_supabase = False
                await self._initialize_sqlite()
                
            self.is_initialized = True
            logger.info("🎉 Database initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Database initialization failed: {e}")
            raise
    
    async def _try_supabase_connection(self) -> bool:
        """尝试连接Supabase"""
        try:
            from supabase import create_client
            
            self.supabase_client = create_client(
                settings.SUPABASE_URL, 
                settings.SUPABASE_SERVICE_KEY
            )
            
            # 测试连接
            result = self.supabase_client.table('users').select('*').limit(1).execute()
            return True
            
        except Exception as e:
            logger.warning(f"Supabase connection failed: {e}")
            return False
    
    async def _initialize_supabase_tables(self):
        """初始化Supabase表结构"""
        try:
            # 检查表是否存在，如果不存在则创建
            await self._ensure_supabase_tables()
            logger.info("✅ Supabase tables initialized")
        except Exception as e:
            logger.error(f"❌ Supabase tables initialization failed: {e}")
            raise
    
    async def _ensure_supabase_tables(self):
        """确保Supabase表存在"""
        tables_to_check = [
            'users', 'projects', 'data_collection_jobs', 
            'training_jobs', 'collected_data', 'model_exports', 'invitations'
        ]
        
        for table_name in tables_to_check:
            try:
                # 尝试查询表，如果不存在会抛出异常
                result = self.supabase_client.table(table_name).select('*').limit(1).execute()
                logger.info(f"✅ Table {table_name} exists")
            except Exception as e:
                logger.warning(f"⚠️ Table {table_name} might not exist: {e}")
    
    async def _initialize_sqlite(self):
        """初始化SQLite数据库"""
        try:
            # 确保数据库文件夹存在
            db_path = "metra.db"
            
            # 创建SQLAlchemy引擎
            self.engine = create_engine(
                f"sqlite:///{db_path}",
                connect_args={"check_same_thread": False},
                echo=False
            )
            
            # 创建会话
            self.SessionLocal = sessionmaker(
                autocommit=False, 
                autoflush=False, 
                bind=self.engine
            )
            
            # 创建表结构
            await self._create_sqlite_tables()
            logger.info("✅ SQLite database initialized")
            
        except Exception as e:
            logger.error(f"❌ SQLite initialization failed: {e}")
            raise
    
    async def _create_sqlite_tables(self):
        """创建SQLite表结构"""
        try:
            # 创建所有表
            Base.metadata.create_all(bind=self.engine)
            
            # 手动创建表如果需要
            with self.engine.connect() as conn:
                # Users表
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        id TEXT PRIMARY KEY,
                        email TEXT UNIQUE NOT NULL,
                        hashed_password TEXT NOT NULL,
                        full_name TEXT,
                        is_active BOOLEAN DEFAULT TRUE,
                        is_superuser BOOLEAN DEFAULT FALSE,
                        subscription_tier TEXT DEFAULT 'free',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Projects表
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS projects (
                        project_id TEXT PRIMARY KEY,
                        user_id TEXT NOT NULL,
                        name TEXT NOT NULL,
                        description TEXT,
                        task_type TEXT NOT NULL,
                        language TEXT DEFAULT 'english',
                        domain TEXT DEFAULT 'general',
                        status TEXT DEFAULT 'active',
                        settings TEXT DEFAULT '{}',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users(id)
                    )
                """)
                
                # Data Collection Jobs表
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS data_collection_jobs (
                        id TEXT PRIMARY KEY,
                        job_id TEXT UNIQUE NOT NULL,
                        user_id TEXT NOT NULL,
                        project_id TEXT,
                        status TEXT DEFAULT 'pending',
                        progress INTEGER DEFAULT 0,
                        total_count INTEGER DEFAULT 0,
                        collected_count INTEGER DEFAULT 0,
                        sources_progress TEXT DEFAULT '{}',
                        errors TEXT DEFAULT '[]',
                        message TEXT,
                        config TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users(id),
                        FOREIGN KEY (project_id) REFERENCES projects(project_id)
                    )
                """)
                
                # Training Jobs表
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS training_jobs (
                        id TEXT PRIMARY KEY,
                        job_id TEXT UNIQUE NOT NULL,
                        user_id TEXT NOT NULL,
                        project_id TEXT,
                        task_name TEXT NOT NULL,
                        task_description TEXT,
                        base_model TEXT NOT NULL,
                        status TEXT DEFAULT 'pending',
                        progress INTEGER DEFAULT 0,
                        data_count INTEGER DEFAULT 0,
                        training_config TEXT DEFAULT '{}',
                        logs TEXT DEFAULT '[]',
                        metrics TEXT DEFAULT '{}',
                        model_url TEXT,
                        replicate_training_id TEXT,
                        openai_job_id TEXT,
                        exports TEXT DEFAULT '{}',
                        error TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users(id),
                        FOREIGN KEY (project_id) REFERENCES projects(project_id)
                    )
                """)
                
                # Collected Data表
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS collected_data (
                        id TEXT PRIMARY KEY,
                        job_id TEXT NOT NULL,
                        text TEXT NOT NULL,
                        title TEXT,
                        url TEXT,
                        source TEXT,
                        label TEXT DEFAULT 'unknown',
                        confidence REAL DEFAULT 0.0,
                        task_type TEXT,
                        processed_at TIMESTAMP,
                        processed_by TEXT,
                        metadata TEXT DEFAULT '{}',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (job_id) REFERENCES data_collection_jobs(job_id)
                    )
                """)
                
                # Model Exports表
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS model_exports (
                        id TEXT PRIMARY KEY,
                        export_id TEXT UNIQUE NOT NULL,
                        training_job_id TEXT,
                        user_id TEXT NOT NULL,
                        format TEXT NOT NULL,
                        status TEXT DEFAULT 'preparing',
                        progress INTEGER DEFAULT 0,
                        file_path TEXT,
                        download_url TEXT,
                        error TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (training_job_id) REFERENCES training_jobs(id),
                        FOREIGN KEY (user_id) REFERENCES users(id)
                    )
                """)
                
                # Invitations表
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS invitations (
                        id TEXT PRIMARY KEY,
                        email TEXT UNIQUE NOT NULL,
                        invitation_code TEXT UNIQUE NOT NULL,
                        invited_by TEXT,
                        used_at TIMESTAMP,
                        used_by TEXT,
                        expires_at TIMESTAMP,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (invited_by) REFERENCES users(id),
                        FOREIGN KEY (used_by) REFERENCES users(id)
                    )
                """)
                
                conn.commit()
                logger.info("✅ SQLite tables created successfully")
                
        except Exception as e:
            logger.error(f"❌ SQLite tables creation failed: {e}")
            raise
    
    def get_session(self):
        """获取数据库会话"""
        if not self.is_initialized:
            raise Exception("Database not initialized")
            
        if self.is_supabase:
            return self.supabase_client
        else:
            return self.SessionLocal()
    
    def get_connection_status(self) -> Dict[str, Any]:
        """获取数据库连接状态"""
        return {
            "is_initialized": self.is_initialized,
            "database_type": "Supabase" if self.is_supabase else "SQLite",
            "is_supabase": self.is_supabase,
            "connection_healthy": self.is_initialized
        }
    
    async def health_check(self) -> bool:
        """健康检查"""
        try:
            if not self.is_initialized:
                return False
                
            if self.is_supabase:
                # 测试Supabase连接
                result = self.supabase_client.table('users').select('*').limit(1).execute()
                return True
            else:
                # 测试SQLite连接
                with self.engine.connect() as conn:
                    conn.execute("SELECT 1")
                    return True
                    
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False

# 全局数据库管理器实例
db_manager = DatabaseManager()

async def init_database():
    """初始化数据库"""
    await db_manager.initialize()

def get_db():
    """依赖注入：获取数据库会话"""
    return db_manager.get_session()

def get_db_status():
    """获取数据库状态"""
    return db_manager.get_connection_status()