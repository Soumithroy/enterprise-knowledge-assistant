import pytest

from backend.app.services.chunking_service import chunk_text


def test_empty_text_returns_no_chunks():
    assert chunk_text("   ") == []


def test_chunks_respect_size_and_overlap():
    text = "abcdefghij" * 20  # 200 chars
    chunks = chunk_text(text, chunk_size=50, overlap=10)

    assert all(len(chunk) <= 50 for chunk in chunks)
    # consecutive chunks share the overlap region
    assert chunks[0][-10:] == chunks[1][:10]


def test_invalid_overlap_raises():
    with pytest.raises(ValueError):
        chunk_text("hello world", chunk_size=10, overlap=10)
