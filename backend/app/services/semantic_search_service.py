import json
from typing import Any

from backend.app.services.embedding_service import generate_embedding


# Minimum similarity required for a chunk to be considered relevant.
DEFAULT_SIMILARITY_THRESHOLD = 0.35


def calculate_cosine_similarity(
    vector_a: list[float],
    vector_b: list[float],
) -> float:
    """
    Calculate cosine similarity between two normalized vectors.

    Because the embedding vectors are normalized, cosine similarity
    is equivalent to the dot product.
    """
    return sum(a * b for a, b in zip(vector_a, vector_b))


def search_similar_chunks(
    query: str,
    chunks: list[Any],
    top_k: int = 3,
    similarity_threshold: float = DEFAULT_SIMILARITY_THRESHOLD,
) -> list[dict]:
    """
    Search document chunks using semantic similarity.

    Only chunks whose similarity score meets or exceeds the
    configured threshold are returned.
    """

    query_embedding = generate_embedding(query)

    results = []

    for chunk in chunks:
        if not chunk.embedding:
            continue

        chunk_embedding = json.loads(chunk.embedding)

        similarity = calculate_cosine_similarity(
            query_embedding,
            chunk_embedding,
        )

        if similarity < similarity_threshold:
            continue

        results.append(
            {
                "chunk_id": chunk.id,
                "document_id": chunk.document_id,
                "filename": chunk.document.filename,
                "chunk_index": chunk.chunk_index,
                "content": chunk.content,
                "similarity": round(similarity, 4),
            }
        )

    results.sort(
        key=lambda result: result["similarity"],
        reverse=True,
    )

    return results[:top_k]