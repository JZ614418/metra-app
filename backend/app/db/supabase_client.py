"""
Supabase Client Configuration and Database Service
"""

import os
from typing import Dict, List, Optional, Any
from datetime import datetime
from supabase import create_client, Client
from sqlalchemy import create_engine, MetaData, Table, Column, String, Integer, DateTime, Text, Boolean, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Supabase configuration
SUPABASE_URL = "https://lcoxwbeeuukryxtdfljc.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imxjb3h3YmVldXVrcnl4dGRmbGpjIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTA3MTc3NjEsImV4cCI6MjA2NjI5Mzc2MX0.D5lh1A0pnfg43exSr63uqPAxrg2nVWtZ3ajq7310rdY"
SUPABASE_SERVICE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imxjb3h3YmVldXVrcnl4dGRmbGpjIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1MDcxNzc2MSwiZXhwIjoyMDY2MjkzNzYxfQ.5ZkOQaaebpGKnce6PL7bekaatpbV6aO5ezW-MmG47lc"

class SupabaseService:
    """Service for interacting with Supabase database"""
    
    def __init__(self):
        self.client: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
        self.anon_client: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        
    async def ensure_tables_exist(self):
        """Create tables if they don't exist"""
        try:
            # Check if tables exist, if not create them
            await self._create_users_table()
            await self._create_projects_table()
            await self._create_data_collection_jobs_table()
            await self._create_training_jobs_table()
            await self._create_collected_data_table()
            logger.info("All Supabase tables ensured to exist")
        except Exception as e:
            logger.error(f"Error ensuring tables exist: {e}")
            raise
    
    async def _create_users_table(self):
        """Create users table if not exists"""
        try:
            # Users table structure
            result = self.client.table('users').select('*').limit(1).execute()
            if result.data is None:
                logger.info("Creating users table...")
        except Exception as e:
            logger.info(f"Users table might not exist, will be created: {e}")
    
    async def _create_projects_table(self):
        """Create projects table if not exists"""
        try:
            result = self.client.table('projects').select('*').limit(1).execute()
            if result.data is None:
                logger.info("Creating projects table...")
        except Exception as e:
            logger.info(f"Projects table might not exist, will be created: {e}")
    
    async def _create_data_collection_jobs_table(self):
        """Create data collection jobs table if not exists"""
        try:
            result = self.client.table('data_collection_jobs').select('*').limit(1).execute()
            if result.data is None:
                logger.info("Creating data_collection_jobs table...")
        except Exception as e:
            logger.info(f"Data collection jobs table might not exist, will be created: {e}")
    
    async def _create_training_jobs_table(self):
        """Create training jobs table if not exists"""
        try:
            result = self.client.table('training_jobs').select('*').limit(1).execute()
            if result.data is None:
                logger.info("Creating training_jobs table...")
        except Exception as e:
            logger.info(f"Training jobs table might not exist, will be created: {e}")
    
    async def _create_collected_data_table(self):
        """Create collected data table if not exists"""
        try:
            result = self.client.table('collected_data').select('*').limit(1).execute()
            if result.data is None:
                logger.info("Creating collected_data table...")
        except Exception as e:
            logger.info(f"Collected data table might not exist, will be created: {e}")
    
    # Data Collection Jobs
    async def create_data_collection_job(self, job_data: Dict) -> str:
        """Create a new data collection job"""
        try:
            result = self.client.table('data_collection_jobs').insert(job_data).execute()
            if result.data:
                return result.data[0]['job_id']
            else:
                raise Exception("Failed to create data collection job")
        except Exception as e:
            logger.error(f"Error creating data collection job: {e}")
            raise
    
    async def get_data_collection_job(self, job_id: str) -> Optional[Dict]:
        """Get data collection job by ID"""
        try:
            result = self.client.table('data_collection_jobs').select('*').eq('job_id', job_id).execute()
            if result.data:
                return result.data[0]
            return None
        except Exception as e:
            logger.error(f"Error getting data collection job {job_id}: {e}")
            return None
    
    async def update_data_collection_job(self, job_id: str, updates: Dict) -> bool:
        """Update data collection job"""
        try:
            updates['updated_at'] = datetime.utcnow().isoformat()
            result = self.client.table('data_collection_jobs').update(updates).eq('job_id', job_id).execute()
            return result.data is not None
        except Exception as e:
            logger.error(f"Error updating data collection job {job_id}: {e}")
            return False
    
    async def get_user_data_collection_jobs(self, user_id: str) -> List[Dict]:
        """Get all data collection jobs for a user"""
        try:
            result = self.client.table('data_collection_jobs').select('*').eq('user_id', user_id).order('created_at', desc=True).execute()
            return result.data or []
        except Exception as e:
            logger.error(f"Error getting user data collection jobs: {e}")
            return []
    
    # Training Jobs
    async def create_training_job(self, job_data: Dict) -> str:
        """Create a new training job"""
        try:
            result = self.client.table('training_jobs').insert(job_data).execute()
            if result.data:
                return result.data[0]['job_id']
            else:
                raise Exception("Failed to create training job")
        except Exception as e:
            logger.error(f"Error creating training job: {e}")
            raise
    
    async def get_training_job(self, job_id: str) -> Optional[Dict]:
        """Get training job by ID"""
        try:
            result = self.client.table('training_jobs').select('*').eq('job_id', job_id).execute()
            if result.data:
                return result.data[0]
            return None
        except Exception as e:
            logger.error(f"Error getting training job {job_id}: {e}")
            return None
    
    async def update_training_job(self, job_id: str, updates: Dict) -> bool:
        """Update training job"""
        try:
            updates['updated_at'] = datetime.utcnow().isoformat()
            result = self.client.table('training_jobs').update(updates).eq('job_id', job_id).execute()
            return result.data is not None
        except Exception as e:
            logger.error(f"Error updating training job {job_id}: {e}")
            return False
    
    async def get_user_training_jobs(self, user_id: str) -> List[Dict]:
        """Get all training jobs for a user"""
        try:
            result = self.client.table('training_jobs').select('*').eq('user_id', user_id).order('created_at', desc=True).execute()
            return result.data or []
        except Exception as e:
            logger.error(f"Error getting user training jobs: {e}")
            return []
    
    # Collected Data
    async def store_collected_data(self, job_id: str, data_items: List[Dict]) -> bool:
        """Store collected data items for a job"""
        try:
            # Add job_id to each data item
            for item in data_items:
                item['job_id'] = job_id
                item['created_at'] = datetime.utcnow().isoformat()
            
            # Insert in batches to avoid large payloads
            batch_size = 100
            for i in range(0, len(data_items), batch_size):
                batch = data_items[i:i + batch_size]
                result = self.client.table('collected_data').insert(batch).execute()
                if not result.data:
                    logger.error(f"Failed to insert batch {i//batch_size + 1}")
                    return False
            
            return True
        except Exception as e:
            logger.error(f"Error storing collected data: {e}")
            return False
    
    async def get_collected_data(self, job_id: str, skip: int = 0, limit: int = 100) -> List[Dict]:
        """Get collected data for a job with pagination"""
        try:
            result = self.client.table('collected_data').select('*').eq('job_id', job_id).range(skip, skip + limit - 1).execute()
            return result.data or []
        except Exception as e:
            logger.error(f"Error getting collected data: {e}")
            return []
    
    async def get_collected_data_count(self, job_id: str) -> int:
        """Get count of collected data items for a job"""
        try:
            result = self.client.table('collected_data').select('*', count='exact').eq('job_id', job_id).execute()
            return result.count or 0
        except Exception as e:
            logger.error(f"Error getting collected data count: {e}")
            return 0
    
    async def delete_collected_data(self, job_id: str) -> bool:
        """Delete all collected data for a job"""
        try:
            result = self.client.table('collected_data').delete().eq('job_id', job_id).execute()
            return True
        except Exception as e:
            logger.error(f"Error deleting collected data: {e}")
            return False
    
    # Projects
    async def create_project(self, project_data: Dict) -> str:
        """Create a new project"""
        try:
            result = self.client.table('projects').insert(project_data).execute()
            if result.data:
                return result.data[0]['project_id']
            else:
                raise Exception("Failed to create project")
        except Exception as e:
            logger.error(f"Error creating project: {e}")
            raise
    
    async def get_project(self, project_id: str) -> Optional[Dict]:
        """Get project by ID"""
        try:
            result = self.client.table('projects').select('*').eq('project_id', project_id).execute()
            if result.data:
                return result.data[0]
            return None
        except Exception as e:
            logger.error(f"Error getting project {project_id}: {e}")
            return None
    
    async def update_project(self, project_id: str, updates: Dict) -> bool:
        """Update project"""
        try:
            updates['updated_at'] = datetime.utcnow().isoformat()
            result = self.client.table('projects').update(updates).eq('project_id', project_id).execute()
            return result.data is not None
        except Exception as e:
            logger.error(f"Error updating project {project_id}: {e}")
            return False
    
    async def get_user_projects(self, user_id: str) -> List[Dict]:
        """Get all projects for a user"""
        try:
            result = self.client.table('projects').select('*').eq('user_id', user_id).order('created_at', desc=True).execute()
            return result.data or []
        except Exception as e:
            logger.error(f"Error getting user projects: {e}")
            return []
    
    # DFE specific methods
    async def get_all_completed_jobs(self) -> List[Dict]:
        """Get all completed data collection jobs for DFE"""
        try:
            result = self.client.table('data_collection_jobs').select('*').eq('status', 'completed').order('created_at', desc=True).execute()
            return result.data or []
        except Exception as e:
            logger.error(f"Error getting completed jobs: {e}")
            return []
    
    async def save_collected_data(self, data_item: Dict) -> bool:
        """Save a single collected data item"""
        try:
            data_item['created_at'] = datetime.utcnow().isoformat()
            result = self.client.table('collected_data').insert(data_item).execute()
            return result.data is not None
        except Exception as e:
            logger.error(f"Error saving collected data item: {e}")
            return False
    
    async def get_collected_data(self, job_id: str, skip: int = 0, limit: int = 100) -> Dict:
        """Get collected data with pagination info"""
        try:
            # Get total count first
            count_result = self.client.table('collected_data').select('*', count='exact').eq('task_id', job_id).execute()
            total_count = count_result.count or 0
            
            # Get paginated data
            result = self.client.table('collected_data').select('*').eq('task_id', job_id).range(skip, skip + limit - 1).execute()
            
            return {
                "data": result.data or [],
                "total": total_count,
                "skip": skip,
                "limit": limit
            }
        except Exception as e:
            logger.error(f"Error getting collected data: {e}")
            return {"data": [], "total": 0, "skip": skip, "limit": limit}

# Global instance
supabase_service = SupabaseService()