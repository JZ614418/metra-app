# Metra Backend

Backend API for Metra Language Model Training Platform.

## 🚀 Quick Start

1. **Install dependencies**:
```bash
pip install -r requirements.txt
```

2. **Set up environment variables**:
```bash
source local_env.sh
```

3. **Run the server**:
```bash
uvicorn app.main:app --reload --port 8000
```

## 📧 Email Service

Metra uses Resend for sending transactional emails. The email service is configured and ready to use.

### Available Email Functions:

1. **Welcome Email** - Sent when a new user registers
2. **Password Reset Email** - Sent when user requests password reset
3. **Training Complete Email** - Sent when model training is finished

### Usage Example:

```python
from app.services.email import email_service

# Send welcome email
await email_service.send_welcome_email(
    to_email="user@example.com",
    user_name="John Doe"
)

# Send password reset email
await email_service.send_password_reset_email(
    to_email="user@example.com",
    reset_token="reset-token-123"
)

# Send training complete notification
await email_service.send_training_complete_email(
    to_email="user@example.com",
    user_name="John Doe",
    model_name="My Custom Model",
    accuracy=0.95,
    training_time="1 hour 30 minutes"
)
```

### Testing Email Service:

```bash
cd backend
source local_env.sh
python test_email_service.py
```

## 🔑 API Endpoints

### Authentication
- `POST /api/v1/auth/register` - User registration
- `POST /api/v1/auth/login` - User login
- `GET /api/v1/auth/me` - Get current user
- `GET /api/v1/auth/me/usage` - Get usage statistics

### Conversations
- `POST /api/v1/conversations` - Create conversation
- `GET /api/v1/conversations/{id}` - Get conversation
- `POST /api/v1/conversations/{id}/messages` - Send message
- `POST /api/v1/conversations/{id}/complete` - Mark as complete

### Task Definitions
- `POST /api/v1/task-definitions` - Create task
- `GET /api/v1/task-definitions` - List tasks

### Model Recommendations
- `POST /api/v1/recommendations/recommend` - Get model recommendations

### Data Collection
- `POST /api/v1/data-collection/web-scraping` - Start web scraping
- `POST /api/v1/data-collection/ai-generate` - Generate AI data
- `POST /api/v1/data-collection/file-upload` - Upload file
- `GET /api/v1/data-collection/job/{job_id}` - Get job status

## 📚 Documentation

Visit `/docs` for interactive API documentation (Swagger UI).

## 🛠️ Development

### Database Migrations
```bash
# Create migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head
```

### Running Tests
```bash
pytest
```

## 🚀 Deployment

The backend is configured for deployment on:
- Railway (recommended)
- Render
- Any platform supporting Python/FastAPI

## Features
- JWT Authentication
- Conversation Management  
- AI Model Recommendations
- Task Definition Builder

## Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
source local_env.sh

# Run server
uvicorn app.main:app --reload --port 8000
```

## Deployment
Deployed on Render.com with automatic builds from GitHub.

## API Documentation
Once running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc 