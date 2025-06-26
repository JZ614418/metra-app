#!/bin/bash
cd metra-backend
source venv/bin/activate
echo "Starting FastAPI server..."
INNGEST_DEV=1 uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
