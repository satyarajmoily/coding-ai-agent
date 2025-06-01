"""
Configuration management for the Coding AI Agent.

Clean Pydantic BaseSettings implementation that loads all configuration
from .env file with proper validation and type conversion.
"""

from typing import List, Optional
from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings
import os
from pathlib import Path


class Settings(BaseSettings):
    """
    Clean settings for the Coding AI Agent.
    
    All settings loaded from .env file with proper Pydantic validation.
    """
    
    # Application settings
    environment: str = Field(description="Environment: development, staging, production")
    log_level: str = Field(description="Logging level")
    debug_mode: bool = Field(description="Enable debug mode")
    
    # Agent settings
    agent_name: str = Field(description="Agent name")
    agent_port: int = Field(description="Agent port", alias="AGENT_PORT")
    service_name: str = Field(description="Service name")
    service_version: str = Field(description="Service version")
    
    # LLM settings
    llm_provider: str = Field(description="LLM provider")
    llm_model: str = Field(description="LLM model name")
    llm_temperature: float = Field(description="LLM temperature")
    llm_max_tokens: int = Field(description="Maximum tokens")
    llm_timeout: int = Field(description="LLM timeout")
    openai_api_key: Optional[str] = Field(default=None, description="OpenAI API key")
    anthropic_api_key: Optional[str] = Field(default=None, description="Anthropic API key")
    
    # Workspace settings
    workspace_base_path: str = Field(description="Base path for workspaces")
    max_concurrent_tasks: int = Field(description="Maximum concurrent tasks")
    workflow_timeout: int = Field(description="Workflow timeout in seconds")
    testing_timeout: int = Field(description="Testing timeout in seconds")
    
    # GitHub settings
    github_user_name: str = Field(description="GitHub username")
    github_user_email: str = Field(description="GitHub email")
    github_token: str = Field(description="GitHub personal access token")
    target_repositories_raw: str = Field(description="Comma-separated list of target repositories", alias="TARGET_REPOSITORIES")
    
    # CORS settings
    cors_origins_raw: str = Field(description="Comma-separated list of CORS origins", alias="CORS_ORIGINS")
    
    # Computed properties
    api_host: str = Field(default="0.0.0.0", description="API host address")
    
    @field_validator("llm_temperature")
    @classmethod
    def validate_temperature(cls, v):
        """Validate LLM temperature is between 0 and 1."""
        if not 0 <= v <= 1:
            raise ValueError("LLM temperature must be between 0 and 1")
        return v
    
    @field_validator("workspace_base_path")
    @classmethod
    def validate_workspace_path(cls, v):
        """Ensure workspace base path is absolute."""
        if not os.path.isabs(v):
            raise ValueError("Workspace base path must be absolute")
        return v
    
    @model_validator(mode='after')
    def validate_llm_config(self):
        """Validate LLM configuration is complete."""
        if self.llm_provider == 'openai' and not self.openai_api_key:
            raise ValueError("OpenAI API key is required when using OpenAI provider")
        elif self.llm_provider == 'anthropic' and not self.anthropic_api_key:
            raise ValueError("Anthropic API key is required when using Anthropic provider")
        return self
    
    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.environment.lower() == "development"
    
    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.environment.lower() == "production"
    
    @property
    def workspace_path(self) -> str:
        """Get the workspace path, creating it if it doesn't exist."""
        os.makedirs(self.workspace_base_path, exist_ok=True)
        return self.workspace_base_path
    
    @property
    def target_repositories_list(self) -> List[str]:
        """Get target repositories as a list."""
        return [repo.strip() for repo in self.target_repositories_raw.split(',') if repo.strip()]
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Get CORS origins as a list."""
        if self.cors_origins_raw == "*":
            return ["*"]
        return [origin.strip() for origin in self.cors_origins_raw.split(',') if origin.strip()]
    
    # Compatibility properties for existing code
    @property
    def github_username(self) -> str:
        return self.github_user_name
    
    @property
    def github_email(self) -> str:
        return self.github_user_email
    
    @property
    def api_port(self) -> int:
        return self.agent_port
    
    @property
    def cors_origins(self) -> List[str]:
        return self.cors_origins_list
    
    # For backward compatibility - provide target_repositories as list
    @property
    def target_repositories(self) -> List[str]:
        return self.target_repositories_list
    
    def validate_required_settings(self) -> List[str]:
        """
        Validate that all required settings are present.
        
        Returns:
            List of missing required settings
        """
        missing = []
        
        if not self.openai_api_key and self.llm_provider == "openai":
            missing.append("OPENAI_API_KEY")
        
        if not self.anthropic_api_key and self.llm_provider == "anthropic":
            missing.append("ANTHROPIC_API_KEY")
        
        if not self.github_token:
            missing.append("GITHUB_TOKEN")
        
        return missing
    
    class Config:
        # Proper .env file path resolution for container environment
        env_file = Path(__file__).parent.parent.parent.parent / ".env"
        case_sensitive = False
        extra = "ignore"
        
        # Field aliases are defined in Field(alias=...) above


# Global settings instance
_settings_instance = None

def get_settings() -> Settings:
    """Get the global settings instance"""
    global _settings_instance
    if _settings_instance is None:
        _settings_instance = Settings()
    return _settings_instance


def validate_settings() -> None:
    """
    Validate all required settings and raise an error if any are missing.
    
    Raises:
        ValueError: If required settings are missing
    """
    missing = get_settings().validate_required_settings()
    if missing:
        raise ValueError(
            f"Missing required environment variables: {', '.join(missing)}\n"
            f"Please set these in your .env file or environment."
        )