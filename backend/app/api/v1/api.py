from fastapi import APIRouter

from app.api.v1.endpoints import auth, conversations, recommendations

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(conversations.router, prefix="/conversations", tags=["conversations"])
api_router.include_router(recommendations.router, prefix="/recommend", tags=["recommendations"]) 