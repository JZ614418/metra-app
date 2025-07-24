"""
SQLite Database Service
为用户认证、项目管理等提供数据库操作
"""

import sqlite3
import json
import uuid
from typing import Dict, List, Optional, Any
from datetime import datetime
import hashlib
import logging
from contextlib import contextmanager

logger = logging.getLogger(__name__)

class SQLiteService:
    """SQLite数据库服务"""
    
    def __init__(self, db_path: str = "metra.db"):
        self.db_path = db_path
        self.init_db()
    
    def init_db(self):
        """初始化数据库"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("PRAGMA foreign_keys = ON")
                conn.commit()
                logger.info("✅ SQLite database initialized")
        except Exception as e:
            logger.error(f"❌ SQLite initialization failed: {e}")
            raise
    
    @contextmanager
    def get_connection(self):
        """获取数据库连接"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # 返回字典格式
        try:
            yield conn
        finally:
            conn.close()
    
    # 用户管理
    def create_user(self, email: str, password: str, full_name: str = None) -> str:
        """创建用户"""
        try:
            user_id = str(uuid.uuid4())
            hashed_password = self._hash_password(password)
            
            with self.get_connection() as conn:
                conn.execute("""
                    INSERT INTO users (id, email, hashed_password, full_name, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (user_id, email, hashed_password, full_name, datetime.utcnow(), datetime.utcnow()))
                conn.commit()
                
            logger.info(f"✅ User created: {email}")
            return user_id
            
        except sqlite3.IntegrityError as e:
            if "email" in str(e):
                raise ValueError("Email already exists")
            raise
        except Exception as e:
            logger.error(f"❌ User creation failed: {e}")
            raise
    
    def get_user_by_email(self, email: str) -> Optional[Dict]:
        """通过邮箱获取用户"""
        try:
            with self.get_connection() as conn:
                result = conn.execute("""
                    SELECT * FROM users WHERE email = ?
                """, (email,)).fetchone()
                
                if result:
                    return dict(result)
                return None
                
        except Exception as e:
            logger.error(f"❌ Get user by email failed: {e}")
            return None
    
    def get_user_by_id(self, user_id: str) -> Optional[Dict]:
        """通过ID获取用户"""
        try:
            with self.get_connection() as conn:
                result = conn.execute("""
                    SELECT * FROM users WHERE id = ?
                """, (user_id,)).fetchone()
                
                if result:
                    return dict(result)
                return None
                
        except Exception as e:
            logger.error(f"❌ Get user by ID failed: {e}")
            return None
    
    def verify_password(self, email: str, password: str) -> Optional[Dict]:
        """验证密码"""
        try:
            user = self.get_user_by_email(email)
            if user and self._verify_password(password, user['hashed_password']):
                return user
            return None
        except Exception as e:
            logger.error(f"❌ Password verification failed: {e}")
            return None
    
    def update_user(self, user_id: str, updates: Dict) -> bool:
        """更新用户信息"""
        try:
            updates['updated_at'] = datetime.utcnow()
            
            # 构建更新SQL
            set_clause = ", ".join([f"{key} = ?" for key in updates.keys()])
            values = list(updates.values()) + [user_id]
            
            with self.get_connection() as conn:
                conn.execute(f"""
                    UPDATE users SET {set_clause} WHERE id = ?
                """, values)
                conn.commit()
                
            return True
            
        except Exception as e:
            logger.error(f"❌ User update failed: {e}")
            return False
    
    # 项目管理
    def create_project(self, user_id: str, name: str, description: str = None, 
                      task_type: str = "classification", language: str = "english",
                      domain: str = "general") -> str:
        """创建项目"""
        try:
            project_id = str(uuid.uuid4())
            
            with self.get_connection() as conn:
                conn.execute("""
                    INSERT INTO projects (project_id, user_id, name, description, task_type, 
                                        language, domain, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (project_id, user_id, name, description, task_type, language, domain,
                      datetime.utcnow(), datetime.utcnow()))
                conn.commit()
                
            logger.info(f"✅ Project created: {name}")
            return project_id
            
        except Exception as e:
            logger.error(f"❌ Project creation failed: {e}")
            raise
    
    def get_user_projects(self, user_id: str) -> List[Dict]:
        """获取用户的所有项目"""
        try:
            with self.get_connection() as conn:
                results = conn.execute("""
                    SELECT * FROM projects WHERE user_id = ? ORDER BY created_at DESC
                """, (user_id,)).fetchall()
                
                return [dict(row) for row in results]
                
        except Exception as e:
            logger.error(f"❌ Get user projects failed: {e}")
            return []
    
    def get_project(self, project_id: str) -> Optional[Dict]:
        """获取项目"""
        try:
            with self.get_connection() as conn:
                result = conn.execute("""
                    SELECT * FROM projects WHERE project_id = ?
                """, (project_id,)).fetchone()
                
                if result:
                    return dict(result)
                return None
                
        except Exception as e:
            logger.error(f"❌ Get project failed: {e}")
            return None
    
    def update_project(self, project_id: str, updates: Dict) -> bool:
        """更新项目"""
        try:
            updates['updated_at'] = datetime.utcnow()
            
            set_clause = ", ".join([f"{key} = ?" for key in updates.keys()])
            values = list(updates.values()) + [project_id]
            
            with self.get_connection() as conn:
                conn.execute(f"""
                    UPDATE projects SET {set_clause} WHERE project_id = ?
                """, values)
                conn.commit()
                
            return True
            
        except Exception as e:
            logger.error(f"❌ Project update failed: {e}")
            return False
    
    # 数据收集任务
    def create_data_collection_job(self, job_data: Dict) -> str:
        """创建数据收集任务"""
        try:
            job_id = job_data.get('job_id', str(uuid.uuid4()))
            
            with self.get_connection() as conn:
                conn.execute("""
                    INSERT INTO data_collection_jobs (
                        id, job_id, user_id, project_id, status, progress, total_count,
                        collected_count, sources_progress, config, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    str(uuid.uuid4()), job_id, job_data['user_id'], job_data.get('project_id'),
                    job_data.get('status', 'pending'), job_data.get('progress', 0),
                    job_data.get('total_count', 0), job_data.get('collected_count', 0),
                    json.dumps(job_data.get('sources_progress', {})),
                    json.dumps(job_data['config']), datetime.utcnow(), datetime.utcnow()
                ))
                conn.commit()
                
            logger.info(f"✅ Data collection job created: {job_id}")
            return job_id
            
        except Exception as e:
            logger.error(f"❌ Data collection job creation failed: {e}")
            raise
    
    def get_data_collection_job(self, job_id: str) -> Optional[Dict]:
        """获取数据收集任务"""
        try:
            with self.get_connection() as conn:
                result = conn.execute("""
                    SELECT * FROM data_collection_jobs WHERE job_id = ?
                """, (job_id,)).fetchone()
                
                if result:
                    job = dict(result)
                    # 解析JSON字段
                    job['sources_progress'] = json.loads(job['sources_progress'] or '{}')
                    job['config'] = json.loads(job['config'] or '{}')
                    return job
                return None
                
        except Exception as e:
            logger.error(f"❌ Get data collection job failed: {e}")
            return None
    
    def update_data_collection_job(self, job_id: str, updates: Dict) -> bool:
        """更新数据收集任务"""
        try:
            updates['updated_at'] = datetime.utcnow()
            
            # 处理JSON字段
            if 'sources_progress' in updates:
                updates['sources_progress'] = json.dumps(updates['sources_progress'])
            if 'config' in updates:
                updates['config'] = json.dumps(updates['config'])
            
            set_clause = ", ".join([f"{key} = ?" for key in updates.keys()])
            values = list(updates.values()) + [job_id]
            
            with self.get_connection() as conn:
                conn.execute(f"""
                    UPDATE data_collection_jobs SET {set_clause} WHERE job_id = ?
                """, values)
                conn.commit()
                
            return True
            
        except Exception as e:
            logger.error(f"❌ Data collection job update failed: {e}")
            return False
    
    def get_user_data_collection_jobs(self, user_id: str) -> List[Dict]:
        """获取用户的数据收集任务"""
        try:
            with self.get_connection() as conn:
                results = conn.execute("""
                    SELECT * FROM data_collection_jobs WHERE user_id = ? ORDER BY created_at DESC
                """, (user_id,)).fetchall()
                
                jobs = []
                for row in results:
                    job = dict(row)
                    job['sources_progress'] = json.loads(job['sources_progress'] or '{}')
                    job['config'] = json.loads(job['config'] or '{}')
                    jobs.append(job)
                    
                return jobs
                
        except Exception as e:
            logger.error(f"❌ Get user data collection jobs failed: {e}")
            return []
    
    # 辅助方法
    def _hash_password(self, password: str) -> str:
        """哈希密码"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def _verify_password(self, password: str, hashed_password: str) -> bool:
        """验证密码"""
        return hashlib.sha256(password.encode()).hexdigest() == hashed_password
    
    def get_stats(self) -> Dict:
        """获取数据库统计信息"""
        try:
            with self.get_connection() as conn:
                stats = {}
                
                # 用户数量
                stats['users'] = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
                
                # 项目数量
                stats['projects'] = conn.execute("SELECT COUNT(*) FROM projects").fetchone()[0]
                
                # 数据收集任务数量
                stats['data_collection_jobs'] = conn.execute(
                    "SELECT COUNT(*) FROM data_collection_jobs"
                ).fetchone()[0]
                
                # 训练任务数量
                stats['training_jobs'] = conn.execute(
                    "SELECT COUNT(*) FROM training_jobs"
                ).fetchone()[0]
                
                return stats
                
        except Exception as e:
            logger.error(f"❌ Get stats failed: {e}")
            return {}

# 全局实例
sqlite_service = SQLiteService()