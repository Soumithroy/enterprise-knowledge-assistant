import json
from typing import Any

from backend.app.services.embedding_service import generate_embedding


def calculate_cosine_similarity(
    vector_a: list[float],
    vector_b: list[float],
) -> float:
    """
    Calculate cosine similarity between two vectors.

    Since our embeddings are already normalized,
    cosine similarity is simply the dot product.
    """

    return sum(
        a * b
        for a, b in zip(vector_a, vector_b)
    )


def search_similar_chunks(
    query: str,
    chunks: list[Any],
    top_k: int = 3,
) -> list[dict]:
    """
    Find the most semantically similar document chunks.
    """

    # Create an embedding for the user's question
    query_embedding = generate_embedding(query)

    results = []

    # Compare the question against every stored chunk
    for chunk in chunks:

        # Skip chunks that do not have embeddings
        if not chunk.embedding:
            continue

        # Convert JSON text back into a Python list
        chunk_embedding = json.loads(
            chunk.embedding
        )

        # Calculate similarity
        similarity = calculate_cosine_similarity(
            query_embedding,
            chunk_embedding,
        )

        results.append(
            {
                "chunk_id": chunk.id,
                "document_id": chunk.document_id,
                "chunk_index": chunk.chunk_index,
                "content": chunk.content,
                "similarity": round(similarity, 4),
            }
        )

    # Highest similarity first
    results.sort(
        key=lambda result: result["similarity"],
        reverse=True,
    )

    # Return only the top results
    return results[:top_k]