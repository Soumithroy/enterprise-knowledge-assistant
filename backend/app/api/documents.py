import json

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    UploadFile,
)
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.models.document import Document
from backend.app.models.document_chunk import DocumentChunk
from backend.app.services.semantic_search_service import (
    search_similar_chunks,
)
from backend.app.services.chunking_service import chunk_text
from backend.app.services.document_service import extract_text_from_pdf
from backend.app.services.embedding_service import generate_embedding


router = APIRouter(
    prefix="/documents",
    tags=["Documents"],
)


# ============================================================
# UPLOAD DOCUMENT
# ============================================================

@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="Filename is required",
        )

    allowed_extensions = {".pdf", ".txt"}

    extension = "." + file.filename.split(".")[-1].lower()

    if extension not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail="Only PDF and TXT files are supported",
        )

    content = await file.read()

    if extension == ".pdf":
        extracted_text = extract_text_from_pdf(content)
    else:
        extracted_text = content.decode(
            "utf-8",
            errors="ignore",
        )

    if not extracted_text.strip():
        raise HTTPException(
            status_code=400,
            detail="The uploaded document contains no readable text",
        )

    # ========================================================
    # CREATE DOCUMENT
    # ========================================================

    document = Document(
        filename=file.filename,
        content=extracted_text,
    )

    db.add(document)
    db.commit()
    db.refresh(document)

    # ========================================================
    # CREATE CHUNKS
    # ========================================================

    chunks = chunk_text(
        extracted_text,
        chunk_size=500,
        overlap=50,
    )

    # ========================================================
    # ⭐ NEW: CREATE EMBEDDINGS AND SAVE CHUNKS
    # ========================================================

    for index, chunk in enumerate(chunks):

        # ⭐ NEW: Convert this chunk into an embedding
        embedding = generate_embedding(chunk)

        document_chunk = DocumentChunk(
            document_id=document.id,
            chunk_index=index,
            content=chunk,

            # ⭐ NEW: Store the embedding as JSON text
            embedding=json.dumps(embedding),
        )

        db.add(document_chunk)

    db.commit()

    return {
        "id": document.id,
        "filename": document.filename,
        "message": "Document uploaded successfully",
        "characters_extracted": len(extracted_text),
        "chunks_created": len(chunks),

        # ⭐ NEW: Tell us how many embeddings were created
        "embeddings_created": len(chunks),
    }


# ============================================================
# LIST DOCUMENTS
# ============================================================

@router.get("/")
def get_documents(
    db: Session = Depends(get_db),
):
    documents = db.query(Document).all()

    return [
        {
            "id": document.id,
            "filename": document.filename,
            "created_at": document.created_at,
        }
        for document in documents
    ]


# ============================================================
# SEARCH DOCUMENTS
# ============================================================

@router.get("/search")
def search_documents(
    q: str,
    db: Session = Depends(get_db),
):
    if not q.strip():
        return {
            "query": q,
            "count": 0,
            "results": [],
        }

    documents = (
        db.query(Document)
        .filter(Document.content.ilike(f"%{q}%"))
        .all()
    )

    return {
        "query": q,
        "count": len(documents),
        "results": [
            {
                "id": document.id,
                "filename": document.filename,
                "content": document.content,
            }
            for document in documents
        ],
    }

# ============================================================
# SEMANTIC SEARCH
# ============================================================

@router.get("/semantic-search")
def semantic_search(
    q: str,
    top_k: int = 3,
    db: Session = Depends(get_db),
):
    if not q.strip():
        raise HTTPException(
            status_code=400,
            detail="Search query cannot be empty",
        )

    if top_k < 1 or top_k > 10:
        raise HTTPException(
            status_code=400,
            detail="top_k must be between 1 and 10",
        )

    chunks = db.query(DocumentChunk).all()

    if not chunks:
        return {
            "query": q,
            "count": 0,
            "results": [],
        }

    results = search_similar_chunks(
        query=q,
        chunks=chunks,
        top_k=top_k,
    )

    return {
        "query": q,
        "count": len(results),
        "results": results,
    }
# ============================================================
# GET SINGLE DOCUMENT
# ============================================================

@router.get("/{document_id}")
def get_document(
    document_id: int,
    db: Session = Depends(get_db),
):
    document = (
        db.query(Document)
        .filter(Document.id == document_id)
        .first()
    )

    if not document:
        raise HTTPException(
            status_code=404,
            detail="Document not found",
        )

    return {
        "id": document.id,
        "filename": document.filename,
        "content": document.content,
        "created_at": document.created_at,
    }


# ============================================================
# GET DOCUMENT CHUNKS
# ============================================================

@router.get("/{document_id}/chunks")
def get_document_chunks(
    document_id: int,
    db: Session = Depends(get_db),
):
    document = (
        db.query(Document)
        .filter(Document.id == document_id)
        .first()
    )

    if not document:
        raise HTTPException(
            status_code=404,
            detail="Document not found",
        )

    chunks = (
        db.query(DocumentChunk)
        .filter(
            DocumentChunk.document_id == document_id
        )
        .order_by(DocumentChunk.chunk_index)
        .all()
    )

    return {
        "document_id": document_id,
        "filename": document.filename,
        "chunk_count": len(chunks),
        "chunks": [
            {
                "id": chunk.id,
                "chunk_index": chunk.chunk_index,
                "content": chunk.content,

                # ⭐ NEW: Verify an embedding exists
                "has_embedding": chunk.embedding is not None,
            }
            for chunk in chunks
        ],
    }