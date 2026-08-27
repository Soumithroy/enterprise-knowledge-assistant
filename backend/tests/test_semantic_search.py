from backend.app.services.semantic_search_service import (
    calculate_cosine_similarity,
)


def test_cosine_similarity():
    vector_a = [1.0, 0.0, 0.0]
    vector_b = [1.0, 0.0, 0.0]

    similarity = calculate_cosine_similarity(
        vector_a,
        vector_b,
    )

    assert similarity == 1.0


def test_different_vectors():
    vector_a = [1.0, 0.0, 0.0]
    vector_b = [0.0, 1.0, 0.0]

    similarity = calculate_cosine_similarity(
        vector_a,
        vector_b,
    )

    assert similarity == 0.0