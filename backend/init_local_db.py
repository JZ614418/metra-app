import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

# Add the app directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.db.base import Base
from app.core.config import settings

def init_db():
    # Create SQLite database
    engine = create_engine("sqlite:///./metra.db", connect_args={"check_same_thread": False})
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    print("✅ Database initialized successfully!")
    print("📍 Database location: ./metra.db")

if __name__ == "__main__":
    init_db() 