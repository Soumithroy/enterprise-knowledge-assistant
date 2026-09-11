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
from backend.app.services.chunking_service import chunk_text
from backend.app.services.document_service import extract_text_from_pdf
from backend.app.services.embedding_service import generate_embedding


router = APIRouter(
    prefix="/documents",
    tags=["Documents"],
)


# ============================================================
# LIST DOCUMENTS
# ============================================================

@router.get("/")
def get_documents(
    db: Session = Depends(get_db),
):
    """
    Return all uploaded documents with chunk counts.
    """

    documents = (
        db.query(Document)
        .order_by(Document.id.desc())
        .all()
    )

    results = []

    for document in documents:
        chunk_count = (
            db.query(DocumentChunk)
            .filter(
                DocumentChunk.document_id == document.id
            )
            .count()
        )

        results.append(
            {
                "id": document.id,
                "filename": document.filename,
                "created_at": document.created_at,
                "chunk_count": chunk_count,
            }
        )

    return results


# ============================================================
# UPLOAD DOCUMENT
# ============================================================

@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """
    Upload a PDF or TXT document, extract its text,
    create chunks, and generate embeddings.
    """

    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="Filename is required",
        )

    allowed_extensions = {
        ".pdf",
        ".txt",
    }

    extension = (
        "."
        + file.filename.split(".")[-1].lower()
    )

    if extension not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail="Only PDF and TXT files are supported",
        )

    # --------------------------------------------------------
    # Prevent duplicate filenames
    # --------------------------------------------------------

    existing_document = (
        db.query(Document)
        .filter(
            Document.filename == file.filename
        )
        .first()
    )

    if existing_document:
        raise HTTPException(
            status_code=409,
            detail=(
                f"A document named '{file.filename}' "
                "already exists."
            ),
        )

    # --------------------------------------------------------
    # Read uploaded file
    # --------------------------------------------------------

    content = await file.read()

    if not content:
        raise HTTPException(
            status_code=400,
            detail="The uploaded file is empty",
        )

    # --------------------------------------------------------
    # Extract text
    # --------------------------------------------------------

    if extension == ".pdf":
        extracted_text = extract_text_from_pdf(
            content
        )
    else:
        extracted_text = content.decode(
            "utf-8",
            errors="ignore",
        )

    if not extracted_text.strip():
        raise HTTPException(
            status_code=400,
            detail=(
                "The uploaded document contains "
                "no readable text"
            ),
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
    # CREATE EMBEDDINGS
    # ========================================================

    embeddings_created = 0

    for index, chunk_content in enumerate(chunks):

        embedding = generate_embedding(
            chunk_content
        )

        document_chunk = DocumentChunk(
            document_id=document.id,
            chunk_index=index,
            content=chunk_content,
            embedding=str(embedding),
        )

        db.add(document_chunk)

        embeddings_created += 1

    db.commit()

    # ========================================================
    # RETURN UPLOAD RESULT
    # ========================================================

    return {
        "id": document.id,
        "filename": document.filename,
        "message": "Document uploaded successfully",
        "characters_extracted": len(
            extracted_text
        ),
        "chunks_created": len(chunks),
        "embeddings_created": embeddings_created,
    }


# ============================================================
# DELETE DOCUMENT
# ============================================================

@router.delete("/{document_id}")
def delete_document(
    document_id: int,
    db: Session = Depends(get_db),
):
    """
    Delete a document and all associated chunks.
    """

    document = (
        db.query(Document)
        .filter(
            Document.id == document_id
        )
        .first()
    )

    if document is None:
        raise HTTPException(
            status_code=404,
            detail="Document not found",
        )

    # --------------------------------------------------------
    # Delete associated chunks
    # --------------------------------------------------------

    db.query(DocumentChunk).filter(
        DocumentChunk.document_id == document_id
    ).delete(
        synchronize_session=False
    )

    # --------------------------------------------------------
    # Delete document
    # --------------------------------------------------------

    db.delete(document)

    db.commit()

    return {
        "message": "Document deleted successfully",
        "document_id": document_id,
    }