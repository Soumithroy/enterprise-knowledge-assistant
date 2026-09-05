from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api.chat import router as chat_router
from backend.app.api.documents import router as documents_router
from backend.app.core.database import Base, engine

# Import models so SQLAlchemy registers all tables.
from backend.app.models.document import Document
from backend.app.models.document_chunk import DocumentChunk
from backend.app.models.conversation import Conversation
from backend.app.models.conversation_message import ConversationMessage


Base.metadata.create_all(bind=engine)


app = FastAPI(
    title="Enterprise Knowledge Assistant",
    description="RAG-based enterprise document question answering system",
    version="1.0.0",
)


# Allow the React development frontend to communicate
# with the FastAPI backend.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(documents_router)
app.include_router(chat_router)


@app.get("/")
def root():
    return {
        "message": "Enterprise Knowledge Assistant API is running"
    }