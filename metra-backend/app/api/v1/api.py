from fastapi import APIRouter

from app.api.v1.endpoints import auth  # , tasks, models, data, training

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
# api_router.include_router(tasks.router, prefix="/tasks", tags=["tasks"])
# api_router.include_router(models.router, prefix="/models", tags=["models"])
# api_router.include_router(data.router, prefix="/data", tags=["data"])
# api_router.include_router(training.router, prefix="/training", tags=["training"]) 