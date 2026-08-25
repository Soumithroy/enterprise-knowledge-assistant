from sqlalchemy import Column, ForeignKey, Integer, Text
from sqlalchemy.orm import relationship

from backend.app.core.database import Base


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(Integer, primary_key=True, index=True)

    document_id = Column(
        Integer,
        ForeignKey("documents.id"),
        nullable=False,
    )

    chunk_index = Column(
        Integer,
        nullable=False,
    )

    content = Column(
        Text,
        nullable=False,
    )

    document = relationship(
        "Document",
        back_populates="chunks",
    )