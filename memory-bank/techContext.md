# Technical Context - Coding AI Agent

## Technology Stack

### Core Technologies
- **Language**: Python 3.9+
- **Web Framework**: FastAPI 0.104+ for REST API service
- **AI Framework**: LangChain 0.1.0+ for multi-agent coordination
- **LLM Integration**: OpenAI GPT-4 (primary), Anthropic Claude (backup)
- **Git Operations**: GitPython 3.1+ for local git operations
- **GitHub Integration**: PyGithub 1.59+ for PR management and repository operations
- **HTTP Client**: httpx for external API calls and service communication
- **Async Framework**: asyncio with background task management

### AI/LLM Dependencies
- **LangChain**: Multi-agent system orchestration and LLM coordination
- **OpenAI**: GPT-4 for code analysis, planning, and generation
- **LangChain Agents**: Planner, Coder, and Tester agents with specialized prompts
- **Prompt Templates**: Structured prompt management for consistent AI behavior
- **Memory Management**: Context preservation across workflow steps

### Development & Git Dependencies
- **GitPython**: Local git operations (clone, branch, commit, push)
- **PyGithub**: GitHub API integration for repository and PR management
- **Docker**: Container management for isolated testing environments
- **subprocess**: Process management for external command execution
- **pathlib**: File system operations and path management

### Code Quality & Testing
- **pytest**: Testing framework with async support
- **black**: Code formatting for generated code
- **isort**: Import sorting and organization
- **flake8**: Code linting and style checking
- **mypy**: Type checking for generated code
- **coverage**: Test coverage analysis

### Environment & Deployment
- **Docker**: Containerization with Git and development tools
- **docker-py**: Docker API integration for environment management
- **python-dotenv**: Environment variable management
- **pydantic**: Configuration management and data validation
- **uvicorn**: ASGI server for FastAPI application

## Development Setup

### Prerequisites
- Python 3.9 or higher
- Docker (for containerized testing environments)
- Git (for version control operations)
- OpenAI API key (for LLM integration)
- GitHub personal access token (for repository access)
- Access to target repository (market-predictor)

### Local Development Environment
```bash
# Clone repository
git clone <repository-url>
cd AutonomousTradingBuilder/coding-ai-agent

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install -r requirements-dev.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your API keys and configuration

# Run development server
uvicorn src.coding_agent.main:app --reload --host 0.0.0.0 --port 8002
```

### Environment Configuration
```bash
# .env file for local development
ENVIRONMENT=development
LOG_LEVEL=DEBUG
API_HOST=0.0.0.0
API_PORT=8002

# LLM Configuration
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=...
LLM_PROVIDER=openai
LLM_MODEL=gpt-4
LLM_TEMPERATURE=0.1
LLM_MAX_TOKENS=4000

# GitHub Integration
GITHUB_TOKEN=ghp_...
GITHUB_REPOSITORY=user/market-predictor
GITHUB_BASE_URL=https://api.github.com
ALLOWED_REPOSITORIES=user/market-predictor,user/test-repo

# Git Configuration
WORKSPACE_BASE_PATH=/tmp/coding-agent-workspaces
MARKET_PREDICTOR_REPO_URL=https://github.com/user/market-predictor.git
GIT_USER_NAME=Coding AI Agent
GIT_USER_EMAIL=coding-agent@example.com

# Workflow Configuration
WORKFLOW_TIMEOUT=1800  # 30 minutes
TESTING_TIMEOUT=600    # 10 minutes
MAX_CONCURRENT_TASKS=3
CLEANUP_WORKSPACES=true

# Security Configuration
ENABLE_SANDBOXING=true
MAX_WORKSPACE_SIZE=1GB
ALLOWED_FILE_TYPES=.py,.md,.txt,.json,.yml,.yaml
```

### Docker Development
```bash
# Build development image with all tools
docker build -f docker/Dockerfile.dev -t coding-ai-agent:dev .

# Run development container
docker run -p 8002:8002 --env-file .env \
  -v /var/run/docker.sock:/var/run/docker.sock \
  coding-ai-agent:dev

# Run with docker-compose (includes testing environment)
docker-compose -f docker/docker-compose.dev.yml up
```

## Dependencies

### Core Production Dependencies
```
# Web Framework & API
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
pydantic>=2.0.0
pydantic-settings>=2.0.0

# AI/LLM Framework
langchain>=0.1.0
langchain-openai>=0.0.2
openai>=1.0.0
anthropic>=0.7.0

# Git & GitHub Integration
GitPython>=3.1.40
PyGithub>=1.59.0
requests>=2.31.0

# Development Environment
docker>=6.1.0
subprocess-run>=0.1.0

# Utilities
httpx>=0.25.0
python-multipart>=0.0.6
python-dotenv>=1.0.0
asyncio>=3.4.3
pathlib2>=2.3.7
```

### Development Dependencies
```
# Testing Framework
pytest>=7.4.0
pytest-asyncio>=0.21.0
pytest-mock>=3.11.0
pytest-cov>=4.1.0

# Code Quality
black>=23.0.0
isort>=5.12.0
flake8>=6.0.0
mypy>=1.5.0
pre-commit>=3.4.0

# Development Tools
jupyter>=1.0.0  # For LLM experimentation
ipython>=8.14.0  # Interactive development
```

### Specialized Dependencies
```
# Advanced Git Operations
gitdb>=4.0.10
dulwich>=0.21.5

# Enhanced Docker Integration
docker-compose>=1.29.2

# Code Analysis
ast-tools>=0.1.0
rope>=1.9.0  # For code refactoring

# Security & Validation
bandit>=1.7.5  # Security analysis
safety>=2.3.0  # Dependency vulnerability checking
```

## Technical Constraints

### Performance Requirements
- **Workflow Completion**: Complete coding workflow in <15 minutes
- **LLM Response Time**: < 30 seconds for code generation (with timeout)
- **API Response Time**: < 2 seconds for status/health endpoints
- **Environment Setup**: < 2 minutes for testing environment creation
- **Memory Usage**: < 2GB under normal operation (excluding testing environments)

### AI/LLM Constraints
- **Token Limits**: Respect OpenAI token limits (8K for GPT-4)
- **Rate Limiting**: Handle API rate limits with exponential backoff
- **Context Management**: Maintain workflow context within token limits
- **Cost Management**: Monitor and limit LLM usage costs
- **Quality Validation**: Validate all AI-generated code before execution

### Git & Repository Constraints
- **Repository Access**: Limited to explicitly allowed repositories
- **Branch Management**: Automated branch naming with unique identifiers
- **Security Validation**: Validate all repository operations
- **Resource Limits**: Limit workspace size and cleanup after use
- **Timeout Handling**: Appropriate timeouts for all git operations

### Security Requirements
- **Sandboxed Execution**: All code testing in isolated Docker containers
- **Input Validation**: Validate all user inputs and generated code
- **Access Control**: Limited file system and network access
- **Code Analysis**: Security analysis of all generated code
- **Audit Trail**: Complete audit trail of all operations

## Development Workflow

### Code Quality Standards
```bash
# Pre-commit hooks
pre-commit install

# Code formatting
black src/ tests/
isort src/ tests/

# Type checking
mypy src/ --ignore-missing-imports

# Linting
flake8 src/ tests/

# Security analysis
bandit -r src/

# Testing with coverage
pytest tests/ -v --cov=src --cov-report=html
```

### AI Development Workflow
```bash
# Test LLM prompts in Jupyter notebook
jupyter notebook notebooks/

# Validate prompt templates
python scripts/validate_prompts.py

# Test agent workflows with mock LLM
pytest tests/agents/ -k "test_agent_workflow"

# Integration test with real LLM (expensive)
pytest tests/integration/ -m "llm_integration" --slow

# Test git operations
pytest tests/git/ -v
```

### Testing Strategy
```
tests/
├── unit/                    # Unit tests for individual components
│   ├── core/               # Core workflow engine tests
│   ├── services/           # Service layer tests
│   ├── agents/             # Agent tests with mocked LLM
│   └── models/             # Data model tests
├── integration/            # Integration tests
│   ├── api/                # FastAPI endpoint tests
│   ├── git/                # Git operations tests
│   ├── docker/             # Docker environment tests
│   └── llm/                # LLM integration tests (marked as slow)
├── e2e/                    # End-to-end workflow tests
│   ├── simple_features/    # Simple feature implementation tests
│   ├── complex_features/   # Complex feature tests
│   └── error_scenarios/    # Error handling tests
├── fixtures/               # Test data and fixtures
├── mocks/                  # LLM and external service mocks
└── helpers/                # Test utility functions
```

## Configuration Management

### Environment Variables
```python
class Settings(BaseSettings):
    # Application settings
    environment: str = "development"
    log_level: str = "INFO"
    api_host: str = "0.0.0.0"
    api_port: int = 8002
    
    # LLM settings
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    llm_provider: str = "openai"
    llm_model: str = "gpt-4"
    llm_temperature: float = 0.1
    llm_max_tokens: int = 4000
    
    # GitHub settings
    github_token: Optional[str] = None
    github_repository: Optional[str] = None
    github_base_url: str = "https://api.github.com"
    allowed_repositories: List[str] = []
    
    # Git settings
    workspace_base_path: str = "/tmp/coding-agent-workspaces"
    market_predictor_repo_url: str = ""
    git_user_name: str = "Coding AI Agent"
    git_user_email: str = "coding-agent@example.com"
    
    # Workflow settings
    workflow_timeout: int = 1800  # 30 minutes
    testing_timeout: int = 600    # 10 minutes
    max_concurrent_tasks: int = 3
    cleanup_workspaces: bool = True
    
    # Security settings
    enable_sandboxing: bool = True
    max_workspace_size: str = "1GB"
    allowed_file_types: List[str] = [".py", ".md", ".txt", ".json", ".yml", ".yaml"]
    
    class Config:
        env_file = ".env"
        case_sensitive = False
```

### LLM Prompt Management
```python
class PromptTemplates:
    REQUIREMENT_ANALYSIS = """
    You are an expert software engineer analyzing a coding requirement.
    
    Requirement: {requirement}
    Target Service: {target_service}
    Current Codebase Context: {codebase_context}
    
    Analyze this requirement and provide:
    1. Implementation complexity (1-5 scale)
    2. Required files to modify/create
    3. Dependencies needed
    4. Potential risks
    5. Estimated implementation time
    
    Format as JSON:
    {{
        "complexity": 3,
        "files_to_modify": [...],
        "new_files_needed": [...],
        "dependencies": [...],
        "risks": [...],
        "estimated_time_minutes": 15
    }}
    """
    
    CODE_GENERATION = """
    You are an expert Python/FastAPI developer implementing a feature.
    
    Implementation Plan: {plan}
    Target File: {target_file}
    Existing Code Context: {existing_code}
    
    Generate production-quality Python code that:
    - Follows FastAPI best practices
    - Includes proper error handling
    - Has comprehensive type hints
    - Includes docstrings
    - Follows existing code patterns
    
    Return only the code that should be added/modified.
    """
    
    TEST_GENERATION = """
    You are an expert test engineer creating comprehensive tests.
    
    Code to Test: {code_to_test}
    Function/Endpoint: {target_function}
    
    Generate pytest tests that:
    - Test all functionality paths
    - Include edge cases
    - Test error conditions
    - Achieve >95% coverage
    - Use proper fixtures and mocks
    
    Return complete test file content.
    """
```

## Integration Points

### External Service Integrations
- **Market Predictor**: Repository cloning, local testing, health validation
- **GitHub API**: Repository operations, PR creation, branch management
- **OpenAI API**: Code analysis, generation, and validation
- **Docker**: Environment creation, container management, testing isolation

### Service Discovery & Communication
- **Health Endpoints**: Standard health monitoring for integration
- **Status Endpoints**: Detailed workflow status and progress tracking
- **Webhook Integration**: Future integration with external systems
- **Metrics Exposure**: Prometheus metrics for monitoring

### File System & Storage
- **Workspace Management**: Temporary workspace creation and cleanup
- **Code Repository**: Git repository cloning and management
- **Artifact Storage**: Generated code and test results storage
- **Log Management**: Structured logging for debugging and monitoring

## Future Technical Considerations

### Scalability Improvements
- **Multi-Repository Support**: Support for multiple target repositories
- **Parallel Processing**: Handle multiple coding requests simultaneously
- **Resource Optimization**: Efficient workspace and container management
- **Caching Strategies**: Cache code analysis and generation results

### AI/LLM Enhancements
- **Multi-Model Support**: Use different LLMs for different tasks
- **Fine-Tuned Models**: Custom models trained on specific codebases
- **Vector Knowledge Base**: Semantic search for code patterns and solutions
- **Reinforcement Learning**: Learn from implementation success/failure

### Advanced Development Features
- **Code Review AI**: Automated code review and improvement suggestions
- **Refactoring Engine**: Intelligent code refactoring and optimization
- **Documentation Generation**: Automatic API documentation and guides
- **Testing Strategies**: Advanced testing patterns and coverage optimization

### Security Enhancements
- **Zero-Trust Architecture**: Verify all operations and access
- **Enhanced Sandboxing**: More sophisticated isolation mechanisms
- **Vulnerability Scanning**: Automated security analysis of generated code
- **Compliance Checking**: Ensure code meets security and regulatory standards

### Monitoring & Observability
- **Detailed Metrics**: Comprehensive metrics for all operations
- **Distributed Tracing**: Track workflows across multiple services
- **Performance Analytics**: Analyze and optimize workflow performance
- **Cost Tracking**: Monitor and optimize LLM and infrastructure costs

## Container Architecture

### Development Container
```dockerfile
FROM python:3.9-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    docker.io \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Create application user
RUN useradd -m -s /bin/bash coder
RUN usermod -aG docker coder

# Set working directory
WORKDIR /app
COPY . .

# Set proper permissions
RUN chown -R coder:coder /app

USER coder
```

### Testing Environment Container
```dockerfile
FROM python:3.9-slim

# Minimal testing environment
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

# Create isolated test user
RUN useradd -m -s /bin/bash tester

# Security restrictions
RUN echo "tester ALL=(ALL) NOPASSWD: /usr/bin/apt-get" >> /etc/sudoers

USER tester
WORKDIR /home/tester
```

This technical context provides a comprehensive foundation for implementing the Coding AI Agent with proper technology choices, development practices, and security considerations.