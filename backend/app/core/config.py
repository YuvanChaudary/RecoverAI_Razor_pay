"""
RecoverAI — Application Configuration Settings
Pydantic BaseSettings management for local, docker, and production environments.
"""

from functools import lru_cache
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=True,
    )

    # Core Server Settings
    APP_ENV: str = Field(default="development")
    APP_NAME: str = Field(default="RecoverAI")
    API_HOST: str = Field(default="0.0.0.0")
    API_PORT: int = Field(default=8000)
    SECRET_KEY: str = Field(default="recoverai_dev_secret_key_change_in_production_9988776655")
    JWT_SECRET: str = Field(default="recoverai_jwt_secret_key_change_in_production_1122334455")

    # Razorpay Test Credentials
    RAZORPAY_KEY_ID: str = Field(default="rzp_test_mock_key")
    RAZORPAY_KEY_SECRET: str = Field(default="mock_secret")
    RAZORPAY_WEBHOOK_SECRET: str = Field(default="mock_webhook_secret")

    # PostgreSQL Operational Datastore
    POSTGRES_USER: str = Field(default="recovery_admin")
    POSTGRES_PASSWORD: str = Field(default="recovery_pass_secure_dev")
    POSTGRES_DB: str = Field(default="recovery_db")
    POSTGRES_HOST: str = Field(default="localhost")
    POSTGRES_PORT: int = Field(default=5432)
    DATABASE_URL: Optional[str] = Field(default=None)

    @property
    def async_database_url(self) -> str:
        if self.DATABASE_URL:
            # Handle standard postgresql:// to postgresql+asyncpg:// conversion if needed
            if self.DATABASE_URL.startswith("postgresql://"):
                return self.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)
            return self.DATABASE_URL
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    # Temporal Orchestration Engine
    TEMPORAL_HOST: str = Field(default="localhost:7233")
    TEMPORAL_NAMESPACE: str = Field(default="default")
    TEMPORAL_TASK_QUEUE: str = Field(default="recovery-task-queue")

    # AI Engine (NVIDIA NIM / OpenAI)
    NVIDIA_API_KEY: str = Field(default="")
    NVIDIA_MODEL: str = Field(default="meta/llama-3.1-70b-instruct")
    NVIDIA_BASE_URL: str = Field(default="https://integrate.api.nvidia.com/v1")

    # AI Observability (Langfuse)
    LANGFUSE_PUBLIC_KEY: str = Field(default="")
    LANGFUSE_SECRET_KEY: str = Field(default="")
    LANGFUSE_HOST: str = Field(default="https://cloud.langfuse.com")

    # Governance & RegTech (OPA)
    OPA_URL: str = Field(default="http://localhost:8181/v1/data/recovery/governance/allow")

    # Cryptographic Audit Ledger (immudb)
    IMMUDB_HOST: str = Field(default="localhost")
    IMMUDB_PORT: int = Field(default=3322)
    IMMUDB_DATABASE: str = Field(default="defaultdb")
    IMMUDB_USER: str = Field(default="immudb")
    IMMUDB_PASSWORD: str = Field(default="immudb_pass_dev")

    # Notification Engine (Novu)
    NOVU_API_KEY: str = Field(default="")


@lru_cache()
def get_settings() -> Settings:
    return Settings()
