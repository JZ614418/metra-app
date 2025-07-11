from app.db.session import engine
from app.db.base import Base
from app.db.session import SessionLocal
from app.models.user import User
from app.core.security import get_password_hash

def init_db():
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    # Create test user if not exists
    db = SessionLocal()
    try:
        test_user = db.query(User).filter(User.email == "test@example.com").first()
        if not test_user:
            test_user = User(
                email="test@example.com",
                hashed_password=get_password_hash("testpassword"),
                is_active=True,
                is_superuser=False
            )
            db.add(test_user)
            db.commit()
            print("Test user created: test@example.com / testpassword")
    finally:
        db.close()
    
    print("Database initialized successfully!")

if __name__ == "__main__":
    init_db() 