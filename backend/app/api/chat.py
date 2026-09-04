from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.models.document_chunk import DocumentChunk
from backend.app.services.chat_service import build_context
from backend.app.services.llm_service import generate_answer
from backend.app.services.semantic_search_service import (
    search_similar_chunks,
)


router = APIRouter(
    prefix="/chat",
    tags=["Chat"],
)


class ChatRequest(BaseModel):
    question: str
    top_k: int = 3


@router.post("/ask")
def ask_question(
    request: ChatRequest,
    db: Session = Depends(get_db),
):
    if not request.question.strip():
        raise HTTPException(
            status_code=400,
            detail="Question cannot be empty",
        )

    if request.top_k < 1 or request.top_k > 10:
        raise HTTPException(
            status_code=400,
            detail="top_k must be between 1 and 10",
        )

    # Get all document chunks
    chunks = db.query(DocumentChunk).all()

    if not chunks:
        return {
            "question": request.question,
            "answer": (
                "No documents have been uploaded yet."
            ),
            "sources": [],
        }

    # Perform semantic search
    search_results = search_similar_chunks(
        query=request.question,
        chunks=chunks,
        top_k=request.top_k,
    )

    # Build context from search results
    context = build_context(search_results)

    # Generate answer
    answer = generate_answer(
    question=request.question,
    context=context,
)

    return {
        "question": request.question,
        "answer": answer,
        "sources": [
            {
                "document_id": result["document_id"],
                "chunk_id": result["chunk_id"],
                "chunk_index": result["chunk_index"],
                "similarity": result["similarity"],
            }
            for result in search_results
        ],
    }