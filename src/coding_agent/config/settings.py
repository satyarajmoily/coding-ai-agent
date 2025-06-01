"""
Configuration management for the Coding AI Agent.

Handles all environment variables, API keys, and system configuration
using strict .env file loading with no defaults.
"""

from typing import List, Optional
from pydantic import Field, validator
from pydantic_settings import BaseSettings
import os

# Import strict config
from .simple_config import get_config


class Settings(BaseSettings):
    """
    Strict settings for the Coding AI Agent.
    
    All settings must be provided via .env file - NO DEFAULTS in code.
    """
    
    # Application settings - NO DEFAULTS
    environment: str = Field(description="Environment: development, staging, production")
    log_level: str = Field(description="Logging level")
    api_host: str = Field(description="API host address")
    api_port: int = Field(description="API port")
    debug_mode: bool = Field(description="Enable debug mode")
    
    # LLM settings - NO DEFAULTS! All values from .env file
    openai_api_key: Optional[str] = Field(default=None, description="OpenAI API key")
    anthropic_api_key: Optional[str] = Field(default=None, description="Anthropic API key")
    llm_provider: Optional[str] = Field(default=None, description="LLM provider (from .env)")
    llm_model: Optional[str] = Field(default=None, description="LLM model name (from .env)")
    llm_temperature: Optional[float] = Field(default=None, description="LLM temperature (from .env)")
    llm_max_tokens: Optional[int] = Field(default=None, description="Maximum tokens (from .env)")
    llm_timeout: Optional[int] = Field(default=None, description="LLM timeout (from .env)")
    
    # GitHub settings - NO DEFAULTS
    github_token: Optional[str] = Field(default=None, description="GitHub personal access token")
    github_username: str = Field(description="GitHub username")
    github_email: str = Field(description="GitHub email")
    
    # Workspace settings - NO DEFAULTS
    workspace_base_path: str = Field(description="Base path for workspaces")
    max_concurrent_tasks: int = Field(description="Maximum concurrent tasks")
    workflow_timeout: int = Field(description="Workflow timeout in seconds")
    testing_timeout: int = Field(description="Testing timeout in seconds")
    
    # Target repositories - NO DEFAULTS
    target_repositories: List[str] = Field(description="List of target repositories")
    
    def __init__(self, **kwargs):
        """Initialize settings with strict config from .env file."""
        super().__init__(**kwargs)
        
        # Load configuration from .env file using strict config
        try:
            config = get_config()
            
            # Set all values from .env file
            self.environment = config.get('environment')
            self.log_level = config.get('log_level')
            self.debug_mode = config.get('debug_mode')
            
            # Agent settings
            agent_config = config.get_agent_config()
            self.api_host = "0.0.0.0"  # Standard for containers
            self.api_port = agent_config['port']
            
            # LLM settings from .env file
            llm_config = config.get_llm_config()
            self.llm_provider = llm_config['provider']
            self.llm_model = llm_config['model']
            self.llm_temperature = llm_config['temperature']
            self.llm_max_tokens = llm_config['max_tokens']
            self.llm_timeout = llm_config['timeout']
            self.openai_api_key = llm_config['api_key']
            
            # Workspace settings
            workspace_config = config.get_workspace_config()
            self.workspace_base_path = workspace_config['base_path']
            self.max_concurrent_tasks = workspace_config['max_concurrent_tasks']
            self.workflow_timeout = workspace_config['workflow_timeout']
            self.testing_timeout = workspace_config['testing_timeout']
            
            # GitHub settings
            github_config = config.get_github_config()
            self.github_username = github_config['user_name']
            self.github_email = github_config['user_email']
            self.github_token = github_config['token']
            self.target_repositories = github_config['target_repositories']
            
        except Exception as e:
            # FAIL FAST - No fallbacks, no defaults
            raise RuntimeError(f"❌ CRITICAL: Cannot load configuration from .env file: {e}")
    
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