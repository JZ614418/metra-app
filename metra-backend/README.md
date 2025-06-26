# Metra Backend

AI-powered no-code model training platform backend API.

## Tech Stack

- **Framework**: FastAPI
- **Database**: PostgreSQL + Supabase
- **Cache**: Redis (Upstash)
- **Task Queue**: Inngest
- **Python**: 3.10+

## Quick Start

### 1. Setup Virtual Environment

```bash
python3.10 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Environment Variables

```bash
cp example.env .env
# Edit .env with your actual values
```

### 4. Run Development Server

```bash
# Start FastAPI
INNGEST_DEV=1 uvicorn app.main:app --reload

# In another terminal, start Inngest Dev Server
npx inngest-cli@latest dev -u http://127.0.0.1:8000/api/inngest --no-discovery
```

The API will be available at `http://localhost:8000`

## API Documentation

Once the server is running, you can access:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Project Structure

```
metra-backend/
├── app/
│   ├── api/v1/         # API endpoints
│   ├── core/           # Core configurations
│   ├── db/             # Database models and sessions
│   ├── models/         # SQLAlchemy models
│   ├── schemas/        # Pydantic schemas
│   ├── services/       # Business logic
│   └── tasks/          # Async tasks (Inngest)
├── tests/              # Test files
├── alembic/            # Database migrations
├── requirements.txt    # Python dependencies
└── .env               # Environment variables
```

## Key Features

- **Authentication**: JWT-based auth with Supabase
- **Task Management**: Natural language task definition
- **Model Recommendations**: AI-powered model selection
- **Data Processing**: Web scraping, AI synthesis, file uploads
- **Training Integration**: Replicate API for model training
- **Async Tasks**: Background job processing with Inngest

## Testing

```bash
pytest tests/
```

## Deployment

See [Deployment Guide](../Metra_Development_Manual.md#部署指南) for production deployment instructions.

## License

Proprietary - Metra AI 