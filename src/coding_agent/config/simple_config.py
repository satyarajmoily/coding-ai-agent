"""
Strict Configuration Loader for Coding AI Agent
Loads configuration from .env file with NO DEFAULTS - fails fast if values are missing
"""
import os
from pathlib import Path
from typing import Dict, Any, Optional
from dotenv import load_dotenv


class StrictConfig:
    """Strict configuration loader that requires all values from .env file"""
    
    def __init__(self, env_file: Optional[str] = None):
        """
        Initialize the strict config loader
        
        Args:
            env_file: Path to .env file (defaults to .env in project root)
        """
        if env_file is None:
            # Look for .env file in project root
            project_root = Path(__file__).parent.parent.parent
            env_file = project_root / ".env"
        
        if not env_file.exists():
            raise FileNotFoundError(f"❌ CRITICAL: .env file not found at {env_file}")
        
        # Load environment variables from .env file
        load_dotenv(env_file)
        
        self._config = {}
        self._load_config()
    
    def _require_env_var(self, var_name: str, var_type: str = "string") -> Any:
        """Get required environment variable or fail with clear error"""
        value = os.getenv(var_name)
        if value is None or value == "":
            raise ValueError(f"❌ REQUIRED: {var_name} must be set in .env file")
        
        # Type conversion
        try:
            if var_type == "int":
                return int(value)
            elif var_type == "float":
                return float(value)
            elif var_type == "bool":
                return value.lower() in ('true', '1', 'yes', 'on')
            elif var_type == "list":
                return value.split(',') if value else []
            else:
                return value
        except ValueError as e:
            raise ValueError(f"❌ INVALID: {var_name} must be a valid {var_type}, got: {value}")
    
    def _load_config(self):
        """Load configuration from environment variables - NO DEFAULTS"""
        self._config = {
            # Application settings - ALL REQUIRED
            'environment': self._require_env_var('ENVIRONMENT'),
            'log_level': self._require_env_var('LOG_LEVEL'),
            'debug_mode': self._require_env_var('DEBUG_MODE', 'bool'),
            
            # Agent settings - ALL REQUIRED
            'agent': {
                'name': self._require_env_var('AGENT_NAME'),
                'port': self._require_env_var('AGENT_PORT', 'int'),
                'service_name': self._require_env_var('SERVICE_NAME'),
                'service_version': self._require_env_var('SERVICE_VERSION'),
            },
            
            # LLM settings - ALL REQUIRED
            'llm': {
                'provider': self._require_env_var('LLM_PROVIDER'),
                'model': self._require_env_var('LLM_MODEL'),
                'temperature': self._require_env_var('LLM_TEMPERATURE', 'float'),
                'max_tokens': self._require_env_var('LLM_MAX_TOKENS', 'int'),
                'timeout': self._require_env_var('LLM_TIMEOUT', 'int'),
                'api_key': self._require_env_var('OPENAI_API_KEY'),
            },
            
            # Workspace settings - ALL REQUIRED
            'workspace': {
                'base_path': self._require_env_var('WORKSPACE_BASE_PATH'),
                'max_concurrent_tasks': self._require_env_var('MAX_CONCURRENT_TASKS', 'int'),
                'workflow_timeout': self._require_env_var('WORKFLOW_TIMEOUT', 'int'),
                'testing_timeout': self._require_env_var('TESTING_TIMEOUT', 'int'),
            },
            
            # GitHub settings - ALL REQUIRED
            'github': {
                'user_name': self._require_env_var('GITHUB_USER_NAME'),
                'user_email': self._require_env_var('GITHUB_USER_EMAIL'),
                'token': self._require_env_var('GITHUB_TOKEN'),
                'target_repositories': self._require_env_var('TARGET_REPOSITORIES', 'list'),
            }
        }
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key (supports dot notation)"""
        keys = key.split('.')
        value = self._config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def get_llm_config(self) -> Dict[str, Any]:
        """Get LLM configuration"""
        return self._config.get('llm', {})
    
    def get_agent_config(self) -> Dict[str, Any]:
        """Get agent configuration"""
        return self._config.get('agent', {})
    
    def get_workspace_config(self) -> Dict[str, Any]:
        """Get workspace configuration"""
        return self._config.get('workspace', {})
    
    def get_github_config(self) -> Dict[str, Any]:
        """Get GitHub configuration"""
        return self._config.get('github', {})
    
    def to_dict(self) -> Dict[str, Any]:
        """Return the entire configuration as a dictionary"""
        return self._config.copy()


# Global config instance
_config_instance = None

def get_config() -> StrictConfig:
    """Get the global configuration instance"""
    global _config_instance
    if _config_instance is None:
        _config_instance = StrictConfig()
    return _config_instance

def reload_config():
    """Reload the configuration"""
    global _config_instance
    _config_instance = None
    return get_config() 