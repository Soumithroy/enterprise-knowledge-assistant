from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.models.conversation import Conversation
from backend.app.models.conversation_message import ConversationMessage
from backend.app.models.document_chunk import DocumentChunk
from backend.app.services.chat_service import build_context
from backend.app.services.llm_service import generate_answer
from backend.app.services.semantic_search_service import search_similar_chunks


router = APIRouter(
    prefix="/chat",
    tags=["Chat"],
)


class ChatRequest(BaseModel):
    question: str
    conversation_id: int | None = None
    top_k: int = Field(
        default=3,
        ge=1,
        le=10,
    )


@router.get("/conversations")
def get_conversations(
    db: Session = Depends(get_db),
):
    """
    Return all conversations with their messages.
    """
    conversations = (
        db.query(Conversation)
        .order_by(Conversation.id.desc())
        .all()
    )

    return [
        {
            "id": conversation.id,
            "created_at": conversation.created_at,
            "messages": [
                {
                    "id": message.id,
                    "role": message.role,
                    "content": message.content,
                }
                for message in conversation.messages
            ],
        }
        for conversation in conversations
    ]


@router.get("/conversations/{conversation_id}")
def get_conversation(
    conversation_id: int,
    db: Session = Depends(get_db),
):
    """
    Return one conversation and all of its messages.
    """
    conversation = (
        db.query(Conversation)
        .filter(Conversation.id == conversation_id)
        .first()
    )

    if conversation is None:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found",
        )

    return {
        "id": conversation.id,
        "created_at": conversation.created_at,
        "messages": [
            {
                "id": message.id,
                "role": message.role,
                "content": message.content,
            }
            for message in conversation.messages
        ],
    }


@router.post("/ask")
def ask_question(
    request: ChatRequest,
    db: Session = Depends(get_db),
):
    """
    Answer a question using enterprise documents and
    persistent conversation history.
    """
    if not request.question.strip():
        raise HTTPException(
            status_code=400,
            detail="Question cannot be empty",
        )

    # ---------------------------------------------------------
    # Get existing conversation or create a new one
    # ---------------------------------------------------------
    if request.conversation_id is None:
        conversation = Conversation()

        db.add(conversation)
        db.commit()
        db.refresh(conversation)

    else:
        conversation = (
            db.query(Conversation)
            .filter(
                Conversation.id == request.conversation_id
            )
            .first()
        )

        if conversation is None:
            raise HTTPException(
                status_code=404,
                detail="Conversation not found",
            )

    # ---------------------------------------------------------
    # Retrieve previous conversation messages
    # ---------------------------------------------------------
    previous_messages = (
        db.query(ConversationMessage)
        .filter(
            ConversationMessage.conversation_id
            == conversation.id
        )
        .order_by(ConversationMessage.id)
        .all()
    )

    conversation_history = "\n\n".join(
        f"{message.role.upper()}: {message.content}"
        for message in previous_messages
    )

    # ---------------------------------------------------------
    # Save user's new message
    # ---------------------------------------------------------
    user_message = ConversationMessage(
        conversation_id=conversation.id,
        role="user",
        content=request.question,
    )

    db.add(user_message)
    db.commit()

    # ---------------------------------------------------------
    # Retrieve document chunks
    # ---------------------------------------------------------
    chunks = db.query(DocumentChunk).all()

    if not chunks:
        answer = (
            "No documents have been uploaded yet."
        )

        assistant_message = ConversationMessage(
            conversation_id=conversation.id,
            role="assistant",
            content=answer,
        )

        db.add(assistant_message)
        db.commit()

        return {
            "conversation_id": conversation.id,
            "question": request.question,
            "answer": answer,
            "sources": [],
        }

    # ---------------------------------------------------------
    # Semantic document search
    # ---------------------------------------------------------
    search_results = search_similar_chunks(
        query=request.question,
        chunks=chunks,
        top_k=request.top_k,
    )

    if not search_results:
        answer = (
            "I could not find the answer in the "
            "uploaded documents."
        )

        assistant_message = ConversationMessage(
            conversation_id=conversation.id,
            role="assistant",
            content=answer,
        )

        db.add(assistant_message)
        db.commit()

        return {
            "conversation_id": conversation.id,
            "question": request.question,
            "answer": answer,
            "sources": [],
        }

    # ---------------------------------------------------------
    # Build context from retrieved document chunks
    # ---------------------------------------------------------
    context = build_context(search_results)

    # ---------------------------------------------------------
    # Generate answer using local Ollama
    # ---------------------------------------------------------
    answer = generate_answer(
        question=request.question,
        context=context,
        conversation_history=conversation_history,
    )

    # ---------------------------------------------------------
    # Save assistant response
    # ---------------------------------------------------------
    assistant_message = ConversationMessage(
        conversation_id=conversation.id,
        role="assistant",
        content=answer,
    )

    db.add(assistant_message)
    db.commit()

    # ---------------------------------------------------------
    # Return answer + sources
    # ---------------------------------------------------------
    return {
        "conversation_id": conversation.id,
        "question": request.question,
        "answer": answer,
        "sources": [
            {
                "filename": result["filename"],
                "document_id": result["document_id"],
                "chunk_id": result["chunk_id"],
                "chunk_index": result["chunk_index"],
                "similarity": result["similarity"],
            }
            for result in search_results
        ],
    }