"""Test configuration: isolated SQLite DB, offline embeddings and no LLM, so tests are fast and deterministic."""
import os
import tempfile

_tmp_dir = tempfile.mkdtemp()

os.environ.setdefault("DATABASE_URL", f"sqlite:///{_tmp_dir}/test.db")
os.environ.setdefault("EMBEDDING_BACKEND", "hashing")
os.environ.setdefault("LLM_PROVIDER", "extractive")
os.environ.setdefault("SIMILARITY_THRESHOLD", "0.1")
