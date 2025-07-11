from fastapi import APIRouter

from app.api.v1.endpoints import auth, conversations, data_builder, data_collection, dfe, recommendations, training, deployment, training_e2e

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(conversations.router, tags=["conversations"])
api_router.include_router(data_builder.router, prefix="/data-builder", tags=["data-builder"])
api_router.include_router(data_collection.router, prefix="/data-collection", tags=["data-collection"])
api_router.include_router(dfe.router, prefix="/dfe", tags=["dfe"])
api_router.include_router(recommendations.router, prefix="/recommendations", tags=["recommendations"])
api_router.include_router(training.router, prefix="/training", tags=["training"])
api_router.include_router(deployment.router, prefix="/deployment", tags=["deployment"])
api_router.include_router(training_e2e.router, prefix="/training-e2e", tags=["training-e2e"]) 