# Import all SQLAlchemy models here to ensure they are registered
# with SQLAlchemy's mapper before creating tables

from app.db.base_class import Base  # noqa
from app.models.user import User  # noqa
from app.models.conversation import Conversation, Message, TaskDefinition  # noqa 