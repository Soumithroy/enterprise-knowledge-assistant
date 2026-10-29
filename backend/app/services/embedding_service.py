import hashlib
import re
from functools import lru_cache

import numpy as np

from backend.app.core.config import settings

HASHING_DIM = 512


@lru_cache(maxsize=1)
def get_embedding_model():
    # Imported lazily so the API (and tests) can run without torch when using the hashing backend.
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(settings.embedding_model)


def _hashing_embedding(text: str) -> list[float]:
    """Deterministic bag-of-words feature hashing. Lightweight fallback for CI and offline demos."""
    vector = np.zeros(HASHING_DIM, dtype=np.float32)
    words = re.findall(r"[a-z0-9]+", text.lower())
    for token in words + [f"{a}_{b}" for a, b in zip(words, words[1:])]:
        digest = int(hashlib.md5(token.encode()).hexdigest(), 16)
        vector[digest % HASHING_DIM] += 1.0
    norm = np.linalg.norm(vector)
    return (vector / norm if norm else vector).tolist()


def generate_embedding(text: str) -> list[float]:
    if settings.embedding_backend == "hashing":
        return _hashing_embedding(text)

    model = get_embedding_model()

    embedding = model.encode(
        text,
        normalize_embeddings=True,
    )

    return embedding.tolist()
