"""
Configuration management for the Coding AI Agent.

Handles all environment variables, API keys, and system configuration
using Pydantic settings with validation and type safety.
"""

from typing import List, Optional
from pydantic import Field, validator
from pydantic_settings import BaseSettings
import os

# Import simple config
from .simple_config import get_config


class Settings(BaseSettings):
    """
    Comprehensive settings for the Coding AI Agent.
    
    All settings can be overridden via environment variables.
    """
    
    # Application settings
    environment: str = Field(default="development", description="Environment: development, staging, production")
    log_level: str = Field(default="INFO", description="Logging level")
    api_host: str = Field(default="0.0.0.0", description="API host address")
    api_port: int = Field(default=8002, description="API port")
    debug_mode: bool = Field(default=True, description="Enable debug mode")
    
    # LLM settings - NO DEFAULTS! All values from agents.yml
    openai_api_key: Optional[str] = Field(default=None, description="OpenAI API key")
    anthropic_api_key: Optional[str] = Field(default=None, description="Anthropic API key")
    llm_provider: Optional[str] = Field(default=None, description="LLM provider (from agents.yml)")
    llm_model: Optional[str] = Field(default=None, description="LLM model name (from agents.yml)")
    llm_temperature: Optional[float] = Field(default=None, description="LLM temperature (from agents.yml)")
    llm_max_tokens: Optional[int] = Field(default=None, description="Maximum tokens (from agents.yml)")
    llm_timeout: Optional[int] = Field(default=None, description="LLM timeout (from agents.yml)")
    
    # GitHub settings
    github_token: Optional[str] = Field(default=None, description="GitHub personal access token")
    github_username: str = Field(default="satyarajmoily", description="GitHub username")
    github_base_url: str = Field(default="https://api.github.com", description="GitHub API base URL")
    
    # Git settings
    workspace_base_path: str = Field(default="/tmp/coding-agent-workspaces", description="Base path for workspaces")
    git_user_name: str = Field(default="Coding AI Agent", description="Git user name for commits")
    git_user_email: str = Field(default="coding-agent@autonomous-trading.com", description="Git user email")
    
    # Workflow settings
    workflow_timeout: int = Field(default=1800, description="Workflow timeout in seconds (30 minutes)")
    testing_timeout: int = Field(default=600, description="Testing timeout in seconds (10 minutes)")
    max_concurrent_tasks: int = Field(default=3, description="Maximum concurrent coding tasks")
    cleanup_workspaces: bool = Field(default=True, description="Cleanup workspaces after completion")
    
    # Security settings
    enable_sandboxing: bool = Field(default=True, description="Enable sandboxed execution")
    max_workspace_size: str = Field(default="1GB", description="Maximum workspace size")
    allowed_file_types: List[str] = Field(
        default=[".py", ".md", ".txt", ".json", ".yml", ".yaml", ".toml"],
        description="Allowed file types for modification"
    )
    
    # Docker settings
    docker_socket_path: str = Field(default="/var/run/docker.sock", description="Docker socket path")
    docker_image_base: str = Field(default="python:3.9-slim", description="Base Docker image for testing")
    docker_network_mode: str = Field(default="bridge", description="Docker network mode")
    
    # API settings
    api_key: Optional[str] = Field(default=None, description="API key for webhook authentication")
    cors_origins: List[str] = Field(default=["*"], description="CORS allowed origins")
    request_timeout: int = Field(default=300, description="API request timeout in seconds")
    
    def __init__(self, **kwargs):
        """Initialize settings with LLM config from .env file."""
        super().__init__(**kwargs)
        
        # Load LLM configuration from .env file
        try:
            config = get_config()
            llm_config = config.get_llm_config()
            
            # Set LLM settings from .env file
            self.llm_provider = llm_config['provider']
            self.llm_model = llm_config['model']
            self.llm_temperature = llm_config['temperature']
            self.llm_max_tokens = llm_config['max_tokens']
            self.llm_timeout = llm_config['timeout']
            
        except Exception as e:
            # FAIL FAST - No fallbacks, no defaults
            raise RuntimeError(f"❌ CRITICAL: Cannot load LLM configuration from .env file: {e}")
    
    @validator("llm_temperature")
    def validate_temperature(cls, v):
        """Validate LLM temperature is between 0 and 1."""
        if v is not None and not 0 <= v <= 1:
            raise ValueError("LLM temperature must be between 0 and 1")
        return v
    
    @validator("workspace_base_path")
    def validate_workspace_path(cls, v):
        """Ensure workspace base path is absolute."""
        if not os.path.isabs(v):
            raise ValueError("Workspace base path must be absolute")
        return v
    
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
        env_file = ".env"
        case_sensitive = False
        env_prefix = ""
        extra = "ignore"  # Allow extra fields from .env


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get the global settings instance."""
    return settings


def validate_settings() -> None:
    """
    Validate all required settings and raise an error if any are missing.
    
    Raises:
        ValueError: If required settings are missing
    """
    missing = settings.validate_required_settings()
    if missing:
        raise ValueError(
            f"Missing required environment variables: {', '.join(missing)}\n"
            f"Please set these in your .env file or environment."
        )