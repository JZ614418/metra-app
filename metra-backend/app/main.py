import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
# import sentry_sdk
# from sentry_sdk.integrations.fastapi import FastApiIntegration
# from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

from app.api.v1.api import api_router
from app.core.config import settings
# from app.db.init_db import init_db
# import inngest.fast_api
# from app.tasks.inngest_app import (
#     inngest_client, 
#     process_training_job, 
#     process_data_upload,
#     scrape_web_data,
#     reset_monthly_usage,
#     notify_model_deployed
# )

# Initialize Sentry
# if settings.SENTRY_DSN:
#     sentry_sdk.init(
#         dsn=settings.SENTRY_DSN,
#         integrations=[
#             FastApiIntegration(transaction_style="endpoint"),
#             SqlalchemyIntegration(),
#         ],
#         traces_sample_rate=0.1 if settings.ENVIRONMENT == "production" else 1.0,
#         environment=settings.ENVIRONMENT,
#     )

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    # await init_db()
    yield
    # Shutdown
    pass

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan
)

# Set all CORS enabled origins
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Include API router
app.include_router(api_router, prefix=settings.API_V1_STR)

# Serve Inngest endpoint
# inngest.fast_api.serve(
#     app,
#     inngest_client,
#     [
#         process_training_job, 
#         process_data_upload,
#         scrape_web_data,
#         reset_monthly_usage,
#         notify_model_deployed
#     ],
#     serve_path="/api/inngest"
# )

@app.get("/")
async def root():
    return {
        "name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "status": "running"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"} 