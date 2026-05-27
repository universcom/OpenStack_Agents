"""
config/settings.py
─────────────────
Centralised configuration using Pydantic Settings.
All values are read from environment variables / .env file.
"""
from __future__ import annotations

from functools import lru_cache
from typing import List, Literal, Optional

from pydantic import AnyHttpUrl, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

LLMProvider = Literal["anthropic", "openrouter", "ollama"]


class OpenStackSettings(BaseSettings):
    auth_url: AnyHttpUrl = Field("http://localhost:5000/v3", alias="OS_AUTH_URL")
    username: str = Field("admin", alias="OS_USERNAME")
    password: str = Field("admin", alias="OS_PASSWORD")
    project_name: str = Field("admin", alias="OS_PROJECT_NAME")
    user_domain_name: str = Field("Default", alias="OS_USER_DOMAIN_NAME")
    project_domain_name: str = Field("Default", alias="OS_PROJECT_DOMAIN_NAME")
    region_name: str = Field("RegionOne", alias="OS_REGION_NAME")

    model_config = SettingsConfigDict(env_file="config/.env", extra="ignore")

    def to_connection_params(self) -> dict:
        return {
            "auth_url": str(self.auth_url),
            "username": self.username,
            "password": self.password,
            "project_name": self.project_name,
            "user_domain_name": self.user_domain_name,
            "project_domain_name": self.project_domain_name,
            "region_name": self.region_name,
        }


class MonitoringSettings(BaseSettings):
    prometheus_url: AnyHttpUrl = Field("http://localhost:9090", alias="PROMETHEUS_URL")
    opensearch_url: AnyHttpUrl = Field("http://localhost:9200", alias="OPENSEARCH_URL")
    opensearch_username: str = Field("admin", alias="OPENSEARCH_USERNAME")
    opensearch_password: str = Field("admin", alias="OPENSEARCH_PASSWORD")

    model_config = SettingsConfigDict(env_file="config/.env", extra="ignore")


class VectorDBSettings(BaseSettings):
    qdrant_url: AnyHttpUrl = Field("http://localhost:6333", alias="QDRANT_URL")
    qdrant_collection: str = Field("openstack_knowledge", alias="QDRANT_COLLECTION")

    model_config = SettingsConfigDict(env_file="config/.env", extra="ignore")


class AgentSettings(BaseSettings):
    # LLM provider selection. Controls which backend agents/base.py instantiates.
    provider: LLMProvider = Field("anthropic", alias="LLM_PROVIDER")

    # Model identifier — interpretation depends on provider:
    #   anthropic  : "claude-haiku-4-5-20251001", "claude-sonnet-4-6", ...
    #   openrouter : "meta-llama/llama-3.3-70b-instruct:free", "qwen/qwen-2.5-72b-instruct:free", ...
    #   ollama     : "llama3.1:8b", "qwen2.5:14b", ...
    # Falls back to CLAUDE_MODEL for backward compatibility.
    model: Optional[str] = Field(None, alias="LLM_MODEL")
    claude_model: str = Field("claude-haiku-4-5-20251001", alias="CLAUDE_MODEL")

    # Provider-specific credentials / endpoints
    anthropic_api_key: str = Field("sk-ant-test-key", alias="ANTHROPIC_API_KEY")
    openrouter_api_key: str = Field("", alias="OPENROUTER_API_KEY")
    ollama_base_url: str = Field("http://localhost:11434", alias="OLLAMA_BASE_URL")

    # Safety
    dry_run: bool = Field(False, alias="AGENT_DRY_RUN")
    max_batch_size: int = Field(10, alias="AGENT_MAX_BATCH_SIZE")
    approval_required_str: str = Field(
        default="delete_instance,delete_volume,delete_network",
        alias="APPROVAL_REQUIRED",
    )

    @property
    def approval_required(self) -> List[str]:
        """Parse approval_required from comma-separated string."""
        return [item.strip() for item in self.approval_required_str.split(",") if item.strip()]

    @property
    def effective_model(self) -> str:
        """Resolved model name: LLM_MODEL if set, else CLAUDE_MODEL."""
        return self.model or self.claude_model

    model_config = SettingsConfigDict(env_file="config/.env", extra="ignore")


class APISettings(BaseSettings):
    host: str = Field("0.0.0.0", alias="API_HOST")
    port: int = Field(8080, alias="API_PORT")
    secret_key: str = Field("test-secret-key", alias="API_SECRET_KEY")

    model_config = SettingsConfigDict(env_file="config/.env", extra="ignore")


class LogSettings(BaseSettings):
    level: str = Field("INFO", alias="LOG_LEVEL")
    format: str = Field("json", alias="LOG_FORMAT")
    audit_log_path: str = Field("/var/log/openstack-agent/audit.log", alias="AUDIT_LOG_PATH")

    model_config = SettingsConfigDict(env_file="config/.env", extra="ignore")


class Settings(BaseSettings):
    """Root settings — compose all sub-settings."""

    openstack: OpenStackSettings = Field(default_factory=OpenStackSettings)
    monitoring: MonitoringSettings = Field(default_factory=MonitoringSettings)
    vector_db: VectorDBSettings = Field(default_factory=VectorDBSettings)
    agent: AgentSettings = Field(default_factory=AgentSettings)
    api: APISettings = Field(default_factory=APISettings)
    log: LogSettings = Field(default_factory=LogSettings)

    model_config = SettingsConfigDict(env_file="config/.env", extra="ignore")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached singleton Settings instance."""
    return Settings()
