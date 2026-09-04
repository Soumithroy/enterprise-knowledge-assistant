from typing import Any


def build_context(
    search_results: list[dict[str, Any]],
) -> str:
    """
    Build document context from retrieved chunks.
    """

    context_parts = []

    for result in search_results:
        context_parts.append(
            f"Document ID: {result['document_id']}\n"
            f"Chunk: {result['chunk_index']}\n"
            f"Content:\n{result['content']}"
        )

    return "\n\n---\n\n".join(context_parts)