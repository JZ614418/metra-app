# Import all models to ensure they are registered with SQLAlchemy
from .user import User
from .conversation import Conversation, Message, TaskDefinition  
from .data_collection_task import DataCollectionTask, CollectedDataSample

__all__ = [
    "User",
    "Conversation", 
    "Message",
    "TaskDefinition",
    "DataCollectionTask",
    "CollectedDataSample"
]