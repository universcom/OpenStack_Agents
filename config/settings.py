"""
config/settings.py
─────────────────
Centralised configuration using Pydantic Settings.
All values are read from environment variables / .env file.
"""
from __future__ import annotations

from functools import lru_cache
from typing import List

from pydantic import AnyHttpUrl, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class OpenStackSettings(BaseSettings):
    auth_url: AnyHttpUrl = Field(..., alias="OS_AUTH_URL")
    username: str = Field(..., alias="OS_USERNAME")
    password: str = Field(..., alias="OS_PASSWORD")
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
    prometheus_url: AnyHttpUrl = Field(..., alias="PROMETHEUS_URL")
    opensearch_url: AnyHttpUrl = Field(..., alias="OPENSEARCH_URL")
    opensearch_username: str = Field("admin", alias="OPENSEARCH_USERNAME")
    opensearch_password: str = Field(..., alias="OPENSEARCH_PASSWORD")

    model_config = SettingsConfigDict(env_file="config/.env", extra="ignore")


class VectorDBSettings(BaseSettings):
    qdrant_url: AnyHttpUrl = Field(..., alias="QDRANT_URL")
    qdrant_collection: str = Field("openstack_knowledge", alias="QDRANT_COLLECTION")

    model_config = SettingsConfigDict(env_file="config/.env", extra="ignore")


class AgentSettings(BaseSettings):
    anthropic_api_key: str = Field(..., alias="ANTHROPIC_API_KEY")
    claude_model: str = Field("claude-sonnet-4-5", alias="CLAUDE_MODEL")

    # Safety
    dry_run: bool = Field(False, alias="AGENT_DRY_RUN")
    max_batch_size: int = Field(10, alias="AGENT_MAX_BATCH_SIZE")
    approval_required: List[str] = Field(
        default=["delete_instance", "delete_volume", "delete_network"],
        alias="APPROVAL_REQUIRED",
    )

    @field_validator("approval_required", mode="before")
    @classmethod
    def parse_approval_list(cls, v):
        if isinstance(v, str):
            return [item.strip() for item in v.split(",") if item.strip()]
        return v

    model_config = SettingsConfigDict(env_file="config/.env", extra="ignore")


class APISettings(BaseSettings):
    host: str = Field("0.0.0.0", alias="API_HOST")
    port: int = Field(8080, alias="API_PORT")
    secret_key: str = Field(..., alias="API_SECRET_KEY")

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
