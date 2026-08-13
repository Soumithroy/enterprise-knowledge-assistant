from fastapi import FastAPI

from backend.app.core.config import settings


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="AI-powered enterprise knowledge assistant.",
)


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