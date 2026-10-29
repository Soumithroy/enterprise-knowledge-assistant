from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """All runtime configuration comes from environment variables / backend/.env."""

    app_name: str = "Enterprise Knowledge Assistant"
    app_version: str = "1.0.0"
    environment: str = "development"
    debug: bool = True

    # SQLite by default; set to postgresql+psycopg2://user:pass@host/db for PostgreSQL
    database_url: str = "sqlite:///./knowledge_assistant.db"

    # "sentence-transformers" (all-MiniLM-L6-v2) or "hashing" (offline, no model download – used in tests/CI)
    embedding_backend: str = "sentence-transformers"
    embedding_model: str = "all-MiniLM-L6-v2"

    # "ollama" (local LLM), "openai", or "extractive" (no LLM – returns the best matching passages)
    llm_provider: str = "ollama"
    ollama_model: str = "llama3.2"
    ollama_host: str = "http://localhost:11434"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"

    similarity_threshold: float = 0.35
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()
