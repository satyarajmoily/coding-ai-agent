"""Agent Configuration Loader from agents.yml file."""

import os
import yaml
import logging
from typing import Dict, Any, Optional
from pathlib import Path


class AgentsConfigLoader:
    """Load agent-specific configuration from agents.yml file."""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize the config loader.
        
        Args:
            config_path: Path to agents.yml file. If None, uses AGENTS_CONFIG env var.
        """
        self.logger = logging.getLogger(__name__)
        
        # Determine config file path
        if config_path:
            self.config_path = Path(config_path)
        else:
            config_env = os.getenv('AGENTS_CONFIG', '/config/agents.yml')
            self.config_path = Path(config_env)
            
        self.config_data = None
        self._load_config()
    
    def _load_config(self) -> None:
        """Load configuration from agents.yml file."""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r') as f:
                    self.config_data = yaml.safe_load(f)
                self.logger.info(f"✅ Loaded agents configuration from {self.config_path}")
            else:
                raise FileNotFoundError(f"❌ CRITICAL: agents.yml not found at {self.config_path}")
        except Exception as e:
            self.logger.error(f"❌ CRITICAL: Failed to load agents config: {e}")
            raise RuntimeError(f"Cannot start without agents.yml configuration: {e}")
    
    def get_agent_config(self, agent_name: str) -> Dict[str, Any]:
        """Get configuration for a specific agent.
        
        Args:
            agent_name: Name of the agent (e.g., 'coding-ai-agent')
            
        Returns:
            Dictionary containing agent configuration
        """
        if not self.config_data:
            raise RuntimeError("❌ CRITICAL: No configuration data loaded from agents.yml")
            
        # Look in platform_agents section
        platform_agents = self.config_data.get('platform_agents', {})
        agent_config = platform_agents.get(agent_name, {})
        
        if not agent_config:
            raise KeyError(f"❌ CRITICAL: Agent '{agent_name}' not found in agents.yml")
        
        return agent_config
    
    def get_agent_environment_vars(self, agent_name: str) -> Dict[str, str]:
        """Get environment variables for a specific agent from agents.yml.
        
        Args:
            agent_name: Name of the agent
            
        Returns:
            Dictionary of environment variables as key-value pairs
        """
        agent_config = self.get_agent_config(agent_name)
        env_list = agent_config.get('environment', [])
        
        env_dict = {}
        for env_var in env_list:
            if '=' in env_var:
                key, value = env_var.split('=', 1)
                env_dict[key] = value
        
        return env_dict
    
    def get_llm_config(self, agent_name: str) -> Dict[str, Any]:
        """Get LLM configuration for a specific agent.
        
        Args:
            agent_name: Name of the agent
            
        Returns:
            Dictionary containing LLM configuration
        """
        env_vars = self.get_agent_environment_vars(agent_name)
        
        # NO DEFAULTS! Everything must come from agents.yml
        required_keys = ['LLM_PROVIDER', 'LLM_MODEL', 'LLM_TEMPERATURE', 'LLM_MAX_TOKENS', 'LLM_TIMEOUT']
        missing_keys = [key for key in required_keys if key not in env_vars]
        
        if missing_keys:
            raise KeyError(f"❌ CRITICAL: Missing required LLM configuration in agents.yml for {agent_name}: {missing_keys}")
        
        llm_config = {
            'provider': env_vars['LLM_PROVIDER'],
            'model': env_vars['LLM_MODEL'], 
            'temperature': float(env_vars['LLM_TEMPERATURE']),
            'max_tokens': int(env_vars['LLM_MAX_TOKENS']),
            'timeout': int(env_vars['LLM_TIMEOUT'])
        }
        
        self.logger.info(f"🤖 Agent {agent_name} LLM config: {llm_config['provider']}:{llm_config['model']}")
        return llm_config


# Global instance for easy access
_config_loader = None


def get_agents_config() -> AgentsConfigLoader:
    """Get the global agents config loader instance."""
    global _config_loader
    if _config_loader is None:
        _config_loader = AgentsConfigLoader()
    return _config_loader


def get_agent_llm_config(agent_name: str) -> Dict[str, Any]:
    """Convenience function to get LLM config for an agent."""
    return get_agents_config().get_llm_config(agent_name) 