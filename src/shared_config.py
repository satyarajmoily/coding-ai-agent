"""
Shared Configuration Library for AI Agent Platform
Centralized configuration loading for all agents
"""

import os
import yaml
import json
from typing import Dict, List, Optional, Any
from pathlib import Path
from dataclasses import dataclass


@dataclass
class RepositoryConfig:
    """Repository configuration model."""
    name: str
    github_url: str
    type: str
    port: int
    health_endpoint: str
    metrics_endpoint: Optional[str] = None
    coding_enabled: bool = True
    monitoring_enabled: bool = True
    auto_recovery: bool = True
    test_command: Optional[str] = None
    description: Optional[str] = None


@dataclass
class AgentConfig:
    """Agent configuration model."""
    name: str
    enabled: bool
    port: int
    capabilities: List[str]
    target_repositories: str
    environment: List[str]
    volumes: List[str]
    resources: Dict[str, str]
    auto_restart: bool
    health_check: Dict[str, str]


@dataclass
class PlatformConfig:
    """Platform configuration model."""
    name: str
    version: str
    environment: str
    credentials: Dict[str, Any]
    services: Dict[str, Any]
    agent_settings: Dict[str, Any]
    repository_access: Dict[str, Any]
    agents: Dict[str, Any]
    infrastructure: Dict[str, Any]


class CentralizedConfig:
    """Centralized configuration manager for all agents."""
    
    def __init__(self, config_path: str = "/config"):
        """Initialize with configuration path."""
        self.config_path = Path(config_path)
        self._platform_config: Optional[PlatformConfig] = None
        self._repositories: Dict[str, RepositoryConfig] = {}
        self._agents: Dict[str, AgentConfig] = {}
        
    def load_all_configs(self) -> None:
        """Load all configuration files."""
        try:
            self._load_platform_config()
            self._load_repositories_config()
            self._load_agents_config()
        except Exception as e:
            print(f"⚠️  Failed to load configurations: {e}")
            # Fall back to environment variables
            self._load_from_environment()
    
    def _load_platform_config(self) -> None:
        """Load platform configuration."""
        platform_file = self.config_path / "platform.yml"
        if platform_file.exists():
            with open(platform_file, 'r') as f:
                data = yaml.safe_load(f)
                self._platform_config = PlatformConfig(**data)
        
    def _load_repositories_config(self) -> None:
        """Load repositories configuration."""
        repos_file = self.config_path / "repositories.yml"
        if repos_file.exists():
            with open(repos_file, 'r') as f:
                data = yaml.safe_load(f)
                if 'target_repositories' in data:
                    for name, config in data['target_repositories'].items():
                        self._repositories[name] = RepositoryConfig(
                            name=name,
                            **config
                        )
    
    def _load_agents_config(self) -> None:
        """Load agents configuration."""
        agents_file = self.config_path / "agents.yml"
        if agents_file.exists():
            with open(agents_file, 'r') as f:
                data = yaml.safe_load(f)
                if 'platform_agents' in data:
                    for name, config in data['platform_agents'].items():
                        self._agents[name] = AgentConfig(
                            name=name,
                            **config
                        )
    
    def _load_from_environment(self) -> None:
        """Fall back to environment variables."""
        print("📋 Loading configuration from environment variables...")
        
        # Load basic repository from environment
        github_repo = os.getenv('GITHUB_REPOSITORY')
        if github_repo:
            self._repositories['default'] = RepositoryConfig(
                name='default',
                github_url=f"https://github.com/{github_repo}.git",
                type='python',
                port=8000,
                health_endpoint='/health'
            )
    
    def get_all_repositories(self) -> Dict[str, RepositoryConfig]:
        """Get all configured repositories."""
        return self._repositories
    
    def get_allowed_repositories(self) -> List[str]:
        """Get list of allowed repository names."""
        if self._platform_config and 'repository_access' in self._platform_config.repository_access:
            return self._platform_config.repository_access.get('default_repositories', [])
        return list(self._repositories.keys())
    
    def get_repository_config(self, name: str) -> Optional[RepositoryConfig]:
        """Get specific repository configuration."""
        return self._repositories.get(name)
    
    def get_agent_config(self, name: str) -> Optional[AgentConfig]:
        """Get specific agent configuration."""
        return self._agents.get(name)
    
    def get_github_credentials(self) -> Dict[str, str]:
        """Get GitHub credentials from platform config or environment."""
        if self._platform_config and 'credentials' in self._platform_config.__dict__:
            github_creds = self._platform_config.credentials.get('github', {})
            return {
                'token': os.getenv('GITHUB_TOKEN', github_creds.get('token', '')),
                'user_name': os.getenv('GITHUB_USER_NAME', github_creds.get('user_name', '')),
                'user_email': os.getenv('GITHUB_USER_EMAIL', github_creds.get('user_email', ''))
            }
        
        # Fall back to environment variables
        return {
            'token': os.getenv('GITHUB_TOKEN', ''),
            'user_name': os.getenv('GITHUB_USER_NAME', ''),
            'user_email': os.getenv('GITHUB_USER_EMAIL', '')
        }
    
    def get_llm_config(self) -> Dict[str, Any]:
        """Get LLM configuration."""
        if self._platform_config and 'credentials' in self._platform_config.__dict__:
            llm_config = self._platform_config.credentials.get('llm', {})
            return {
                'openai_api_key': os.getenv('OPENAI_API_KEY', llm_config.get('openai_api_key', '')),
                'anthropic_api_key': os.getenv('ANTHROPIC_API_KEY', llm_config.get('anthropic_api_key', '')),
                'provider': llm_config.get('provider', 'openai'),
                'model': llm_config.get('model', 'gpt-4'),
                'temperature': llm_config.get('temperature', 0.1),
                'max_tokens': llm_config.get('max_tokens', 4000),
                'timeout': llm_config.get('timeout', 60)
            }
        
        # Fall back to environment variables
        return {
            'openai_api_key': os.getenv('OPENAI_API_KEY', ''),
            'anthropic_api_key': os.getenv('ANTHROPIC_API_KEY', ''),
            'provider': os.getenv('LLM_PROVIDER', 'openai'),
            'model': os.getenv('LLM_MODEL', 'gpt-4'),
            'temperature': float(os.getenv('LLM_TEMPERATURE', '0.1')),
            'max_tokens': int(os.getenv('LLM_MAX_TOKENS', '4000')),
            'timeout': int(os.getenv('LLM_TIMEOUT', '60'))
        }
    
    def get_allowed_file_types(self) -> List[str]:
        """Get allowed file types."""
        if self._platform_config and 'agent_settings' in self._platform_config.__dict__:
            return self._platform_config.agent_settings.get('allowed_file_types', [])
        
        # Fall back to environment or defaults
        env_types = os.getenv('ALLOWED_FILE_TYPES', '')
        if env_types:
            try:
                return json.loads(env_types)
            except:
                return env_types.split(',')
        
        return ['.py', '.md', '.txt', '.json', '.yml', '.yaml', '.toml']
    
    def get_cors_origins(self) -> List[str]:
        """Get CORS origins."""
        if self._platform_config and 'agent_settings' in self._platform_config.__dict__:
            return self._platform_config.agent_settings.get('cors_origins', ['*'])
        
        # Fall back to environment or defaults
        env_origins = os.getenv('CORS_ORIGINS', '')
        if env_origins:
            try:
                return json.loads(env_origins)
            except:
                return env_origins.split(',')
        
        return ['*']
    
    def get_service_urls(self) -> Dict[str, str]:
        """Get service URLs."""
        if self._platform_config and 'services' in self._platform_config.__dict__:
            services = self._platform_config.services
            return {
                'prometheus': services.get('prometheus', {}).get('url', ''),
                'alertmanager': services.get('alertmanager', {}).get('url', ''),
                'grafana': services.get('grafana', {}).get('url', '')
            }
        
        # Fall back to environment variables
        return {
            'prometheus': os.getenv('PROMETHEUS_URL', 'http://prometheus:9090'),
            'alertmanager': os.getenv('ALERTMANAGER_URL', 'http://alertmanager:9093'),
            'grafana': os.getenv('GRAFANA_URL', 'http://grafana:3000')
        }
    
    def is_multi_repo_mode(self) -> bool:
        """Check if running in multi-repository mode."""
        platform_mode = os.getenv('PLATFORM_MODE', 'single_repo')
        return platform_mode == 'multi_repo'
    
    def summary(self) -> Dict[str, Any]:
        """Get configuration summary."""
        return {
            'platform_config_loaded': self._platform_config is not None,
            'repositories_count': len(self._repositories),
            'agents_count': len(self._agents),
            'multi_repo_mode': self.is_multi_repo_mode(),
            'repositories': list(self._repositories.keys()),
            'agents': list(self._agents.keys()),
            'config_path': str(self.config_path)
        }


# Global instance for easy access
config = CentralizedConfig()

# Initialize configuration on import
config.load_all_configs()
