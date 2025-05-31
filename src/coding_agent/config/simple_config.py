"""
Simple Configuration Loader for Coding AI Agent
Replaces the complex infrastructure config system with simple .env file loading
"""
import os
from pathlib import Path
from typing import Dict, Any, Optional
from dotenv import load_dotenv


class SimpleConfig:
    """Simple configuration loader that reads from .env files"""
    
    def __init__(self, env_file: Optional[str] = None):
        """
        Initialize the simple config loader
        
        Args:
            env_file: Path to .env file (defaults to .env in project root)
        """
        if env_file is None:
            # Look for .env file in project root
            project_root = Path(__file__).parent.parent.parent
            env_file = project_root / ".env"
        
        # Load environment variables from .env file
        load_dotenv(env_file)
        
        self._config = {}
        self._load_config()
    
    def _load_config(self):
        """Load configuration from environment variables"""
        self._config = {
            # Application settings
            'environment': os.getenv('ENVIRONMENT', 'development'),
            'log_level': os.getenv('LOG_LEVEL', 'INFO'),
            'debug_mode': os.getenv('DEBUG_MODE', 'true').lower() == 'true',
            
            # Agent settings
            'agent': {
                'name': os.getenv('AGENT_NAME', 'coding-ai-agent'),
                'port': int(os.getenv('AGENT_PORT', '8002')),
                'service_name': os.getenv('SERVICE_NAME', 'coding-ai-agent'),
                'service_version': os.getenv('SERVICE_VERSION', '0.1.0'),
            },
            
            # LLM settings
            'llm': {
                'provider': os.getenv('LLM_PROVIDER', 'openai'),
                'model': os.getenv('LLM_MODEL', 'gpt-4'),
                'temperature': float(os.getenv('LLM_TEMPERATURE', '0.1')),
                'max_tokens': int(os.getenv('LLM_MAX_TOKENS', '4000')),
                'timeout': int(os.getenv('LLM_TIMEOUT', '60')),
                'api_key': os.getenv('OPENAI_API_KEY'),
            },
            
            # Workspace settings
            'workspace': {
                'base_path': os.getenv('WORKSPACE_BASE_PATH', '/tmp/coding-agent-workspaces'),
                'max_concurrent_tasks': int(os.getenv('MAX_CONCURRENT_TASKS', '3')),
                'workflow_timeout': int(os.getenv('WORKFLOW_TIMEOUT', '1800')),
                'testing_timeout': int(os.getenv('TESTING_TIMEOUT', '600')),
            },
            
            # GitHub settings
            'github': {
                'user_name': os.getenv('GITHUB_USER_NAME', 'satyarajmoily'),
                'user_email': os.getenv('GITHUB_USER_EMAIL', 'satyarajmoily@gmail.com'),
                'token': os.getenv('GITHUB_TOKEN'),
                'target_repositories': os.getenv('TARGET_REPOSITORIES', '').split(','),
            }
        }
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value by key (supports dot notation)
        
        Args:
            key: Configuration key (e.g., 'llm.model' or 'agent.port')
            default: Default value if key not found
            
        Returns:
            Configuration value
        """
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
    
    def get_all_config(self) -> Dict[str, Any]:
        """Get all configuration"""
        return self._config.copy()


# Global config instance
_config_instance = None


def get_config() -> SimpleConfig:
    """Get the global configuration instance"""
    global _config_instance
    if _config_instance is None:
        _config_instance = SimpleConfig()
    return _config_instance


def reload_config():
    """Reload configuration from .env file"""
    global _config_instance
    _config_instance = None
    return get_config() 