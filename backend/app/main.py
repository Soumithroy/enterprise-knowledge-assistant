from fastapi import FastAPI

from backend.app.api.documents import router as documents_router
from backend.app.core.config import settings
from backend.app.core.database import Base, engine
from backend.app.models.document import Document
from backend.app.models.document_chunk import DocumentChunk


# Create database tables
Base.metadata.create_all(bind=engine)


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="AI-powered enterprise knowledge assistant.",
)


app.include_router(documents_router)


@app.get("/")
def root():
    return {
        "message": "Welcome to Enterprise Knowledge Assistant",
        "environment": settings.environment,
    }


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "environment": settings.environment,
    }