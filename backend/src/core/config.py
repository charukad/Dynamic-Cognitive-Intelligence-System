"""Application configuration using Pydantic Settings."""

from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # API Configuration
    api_v1_prefix: str = "/api/v1"
    project_name: str = "DCIS"
    version: str = "0.1.0"
    debug: bool = False

    # CORS
    cors_origins: list[str] = ["http://localhost:3000"]

    # Database - PostgreSQL
    database_url: str = "postgresql://user:password@localhost:5432/dcis"

    # Database - Neo4j
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "devpassword"

    # Database - Redis
    redis_url: str = "redis://localhost:6379"

    # ChromaDB (via HTTP)
    # Local dev: map to exposed port 8001 (container port 8000 mapped to 8001 in docker-compose)
    chroma_host: str = "localhost"
    chroma_port: int = 8001

    # LLM Settings (vLLM / LM Studio / Ollama)
    vllm_api_url: str = "http://localhost:1234/v1"  # LM Studio default
    vllm_api_key: str = "lm-studio"  # Not needed for local, but good practice
    vllm_model_name: str = "mistralai_-_mistral-7b-instruct-v0.2"  # Exact ID required
    use_mock_llm: bool = False  # Set to True if no LLM is running

    # Security
    secret_key: str = "change-this-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # Logging
    log_level: str = "INFO"

    # Chat request controls
    chat_rate_limit_window_seconds: int = 60
    chat_session_read_rate_limit_per_window: int = 120
    chat_session_write_rate_limit_per_window: int = 60
    chat_message_read_rate_limit_per_window: int = 240
    chat_message_write_rate_limit_per_window: int = 60
    chat_message_send_rate_limit_per_window: int = 30
    chat_feedback_rate_limit_per_window: int = 60
    chat_websocket_send_rate_limit_per_window: int = 30

    @property
    def chroma_url(self) -> str:
        """Get ChromaDB URL."""
        return f"http://{self.chroma_host}:{self.chroma_port}"


# Global settings instance
settings = Settings()
