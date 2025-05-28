# System Patterns - Coding AI Agent

## System Architecture

### High-Level Coding AI Agent Architecture
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ API Requirements│────│ Workflow Engine │───│  LangChain LLM  │
│   Interface     │    │  (Orchestrator) │    │ (Code Analysis) │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                │
                       ┌─────────────────┐    ┌─────────────────┐
                       │  Git Operations │────│ Local Testing   │
                       │  (Branch/PR)    │    │   Environment   │
                       └─────────────────┘    └─────────────────┘
```

### Agent Application Architecture
```
src/coding_agent/
├── main.py                         # FastAPI application factory
├── core/                           # Core workflow orchestration
│   ├── workflow_engine.py         # Main developer workflow
│   ├── code_analyzer.py           # Codebase analysis engine
│   ├── test_runner.py             # Testing orchestration
│   └── git_manager.py             # Git operations coordination
├── services/                       # External service integrations
│   ├── git_service.py             # Git operations (clone, branch, commit)
│   ├── github_service.py          # GitHub API (PR creation)
│   ├── local_env_service.py       # Environment management
│   └── llm_service.py             # LangChain/LLM integration
├── agents/                         # LangChain agent components
│   ├── planner_agent.py           # Requirement analysis and planning
│   ├── coder_agent.py             # Code generation agent
│   └── tester_agent.py            # Testing validation agent
├── models/                         # Data models
│   ├── requests.py                # API request models
│   ├── workflow.py                # Workflow state models
│   ├── responses.py               # API response models
│   └── git_models.py              # Git operation models
└── config/                         # Configuration
    ├── settings.py                # Pydantic settings
    ├── prompts.py                 # LLM prompts and templates
    └── logging.py                 # Logging configuration
```

## Key Technical Decisions

### 1. Workflow Orchestration: Event-Driven State Machine
**Decision**: Use state machine pattern for developer workflow
**Reasoning**:
- **Clear State Management**: Each workflow step has defined states and transitions
- **Error Recovery**: Easy rollback to previous states on failure
- **Progress Tracking**: Clear visibility into workflow progress
- **Async Operations**: Non-blocking execution of long-running operations
- **Extensibility**: Easy addition of new workflow steps and validation

### 2. Code Generation: Multi-Agent LangChain System
**Decision**: Use specialized LangChain agents for different coding tasks
**Reasoning**:
- **Specialized Intelligence**: Different agents optimized for specific tasks
- **Context Management**: Maintain context across analysis, planning, and implementation
- **Quality Control**: Separate validation agents ensure code quality
- **Flexibility**: Easy to enhance individual agents without affecting others
- **Scalability**: Parallel execution of agent tasks where possible

### 3. Local Testing: Containerized Isolation
**Decision**: Use Docker containers for isolated testing environments
**Reasoning**:
- **Environment Consistency**: Identical testing environment for every execution
- **Dependency Isolation**: No interference between different coding tasks
- **Resource Management**: Controlled resource allocation for testing
- **Security**: Isolated execution prevents system contamination
- **Cleanup**: Easy environment cleanup after testing

### 4. Git Operations: GitPython + GitHub API Integration
**Decision**: Combine GitPython for local operations with GitHub API for PR management
**Reasoning**:
- **Local Control**: Full control over local git operations
- **Remote Integration**: Seamless GitHub integration for PR creation
- **Branch Management**: Automated branch creation with unique naming
- **Commit Quality**: Automated commit message generation
- **PR Automation**: Rich PR descriptions and metadata

## Design Patterns

### 1. Workflow State Machine Pattern
```python
class WorkflowEngine:
    def __init__(self):
        self.states = {
            'INIT': self.initialize_workspace,
            'ANALYZE': self.analyze_requirements,
            'PLAN': self.create_implementation_plan,
            'CODE': self.generate_code,
            'TEST': self.run_tests,
            'VALIDATE': self.validate_implementation,
            'COMMIT': self.commit_changes,
            'PR': self.create_pull_request,
            'COMPLETE': self.finalize_workflow
        }
        self.current_state = 'INIT'
    
    async def execute_workflow(self, task_id: str, requirements: str):
        """Execute complete development workflow with state management"""
        workflow_context = WorkflowContext(task_id, requirements)
        
        while self.current_state != 'COMPLETE':
            try:
                next_state = await self.states[self.current_state](workflow_context)
                await self.transition_to_state(next_state, workflow_context)
            except WorkflowError as e:
                await self.handle_workflow_error(e, workflow_context)
        
        return workflow_context.result
```

### 2. Multi-Agent Coordination Pattern
```python
class AgentCoordinator:
    def __init__(self, llm: LLM):
        self.planner = PlannerAgent(llm)
        self.coder = CoderAgent(llm)
        self.tester = TesterAgent(llm)
        self.reviewer = ReviewerAgent(llm)
    
    async def execute_coding_task(self, requirements: str, codebase: str) -> CodingResult:
        """Coordinate multiple agents for complete coding task"""
        # Planning phase
        plan = await self.planner.create_implementation_plan(requirements, codebase)
        
        # Implementation phase
        code_changes = await self.coder.implement_plan(plan, codebase)
        
        # Testing phase
        test_results = await self.tester.validate_implementation(code_changes)
        
        # Review phase
        review_result = await self.reviewer.review_changes(code_changes, test_results)
        
        return CodingResult(
            plan=plan,
            code_changes=code_changes,
            test_results=test_results,
            review=review_result
        )
```

### 3. Environment Management Pattern
```python
class LocalEnvironmentManager:
    def __init__(self, base_workspace: str):
        self.base_workspace = base_workspace
        self.active_environments = {}
    
    async def create_environment(self, task_id: str) -> Environment:
        """Create isolated development environment"""
        env_path = f"{self.base_workspace}/env-{task_id}"
        
        environment = Environment(
            path=env_path,
            task_id=task_id,
            container=await self.create_container(env_path)
        )
        
        await environment.setup_dependencies()
        await environment.validate_setup()
        
        self.active_environments[task_id] = environment
        return environment
    
    async def cleanup_environment(self, task_id: str):
        """Clean up environment after task completion"""
        if task_id in self.active_environments:
            env = self.active_environments[task_id]
            await env.cleanup()
            del self.active_environments[task_id]
```

### 4. Git Operations Pattern
```python
class GitOperationsManager:
    def __init__(self, repo_url: str, github_token: str):
        self.repo_url = repo_url
        self.github_client = Github(github_token)
    
    async def execute_git_workflow(
        self, 
        workspace: str, 
        feature_name: str, 
        changes: List[CodeChange]
    ) -> GitResult:
        """Execute complete git workflow"""
        # Clone and setup
        repo = await self.clone_repository(workspace)
        await self.pull_latest_master(repo)
        
        # Create feature branch
        branch_name = self.generate_branch_name(feature_name)
        await self.create_branch(repo, branch_name)
        
        # Apply changes
        await self.apply_code_changes(workspace, changes)
        
        # Commit and push
        commit_message = self.generate_commit_message(changes)
        await self.commit_changes(repo, commit_message)
        await self.push_branch(repo, branch_name)
        
        # Create PR
        pr_url = await self.create_pull_request(branch_name, changes)
        
        return GitResult(
            branch_name=branch_name,
            commit_hash=repo.head.commit.hexsha,
            pr_url=pr_url
        )
```

## Component Relationships

### 1. Workflow Execution Flow
```
API Request → Workflow Engine → State Machine → Agent Coordination
     ↓              ↓               ↓                  ↓
Requirements   State Management   Step Execution   Multi-Agent Tasks
Processing     Progress Tracking  Error Handling   Code Generation
Status Updates Environment Setup  Rollback Logic   Quality Validation
```

### 2. Code Generation Flow
```
Requirements → Analysis Agent → Planning Agent → Code Agent → Testing Agent
     ↓              ↓               ↓               ↓             ↓
Natural Language  Codebase Review  Implementation  Code Writing  Validation
Parsing          Pattern Analysis  Strategy        Quality Check Test Execution
Context Extract  File Mapping      Change Planning Documentation Coverage Analysis
```

### 3. Testing and Validation Flow
```
Code Changes → Environment Setup → Service Testing → Quality Gates → PR Creation
     ↓               ↓                  ↓                ↓              ↓
File Changes    Container Creation   Local Service    Code Quality    GitHub API
Dependencies    Virtual Environment  Health Checks    Test Coverage   PR Description
Configuration   Service Installation API Testing      Style Checks    Labels/Reviews
```

## Error Handling Patterns

### 1. Workflow Error Recovery
```python
class WorkflowErrorHandler:
    async def handle_workflow_error(
        self, 
        error: WorkflowError, 
        context: WorkflowContext
    ) -> RecoveryAction:
        """Handle errors with intelligent recovery strategies"""
        
        if error.type == 'COMPILATION_ERROR':
            # Retry code generation with error context
            return RecoveryAction.RETRY_CODE_GENERATION
        
        elif error.type == 'TEST_FAILURE':
            # Analyze test failures and fix issues
            return RecoveryAction.FIX_TEST_ISSUES
        
        elif error.type == 'ENVIRONMENT_ERROR':
            # Recreate environment and retry
            return RecoveryAction.RECREATE_ENVIRONMENT
        
        elif error.type == 'GIT_ERROR':
            # Retry git operations with fresh clone
            return RecoveryAction.RETRY_GIT_OPERATIONS
        
        else:
            # Escalate complex errors to human
            return RecoveryAction.ESCALATE_TO_HUMAN
```

### 2. Code Generation Error Handling
```python
class CodeGenerationErrorHandler:
    async def handle_generation_error(
        self, 
        error: CodeError, 
        context: CodeContext
    ) -> CodeFix:
        """Handle code generation errors with intelligent fixes"""
        
        if error.type == 'SYNTAX_ERROR':
            # Use LLM to fix syntax issues
            fixed_code = await self.llm_service.fix_syntax_error(
                code=context.generated_code,
                error=error.message
            )
            return CodeFix(type='SYNTAX_FIX', code=fixed_code)
        
        elif error.type == 'IMPORT_ERROR':
            # Add missing imports
            imports = await self.analyze_missing_imports(context.generated_code)
            return CodeFix(type='ADD_IMPORTS', imports=imports)
        
        elif error.type == 'TYPE_ERROR':
            # Fix type annotations
            fixed_types = await self.fix_type_annotations(context.generated_code)
            return CodeFix(type='TYPE_FIX', code=fixed_types)
```

### 3. Environment Error Recovery
```python
class EnvironmentErrorHandler:
    async def recover_from_environment_error(
        self, 
        error: EnvironmentError, 
        task_id: str
    ) -> Environment:
        """Recover from environment setup failures"""
        
        # Clean up failed environment
        await self.cleanup_failed_environment(task_id)
        
        # Create new environment with error mitigation
        if error.type == 'DEPENDENCY_ERROR':
            # Use cached dependencies
            return await self.create_environment_with_cache(task_id)
        
        elif error.type == 'PERMISSION_ERROR':
            # Adjust permissions and retry
            return await self.create_environment_with_permissions(task_id)
        
        elif error.type == 'RESOURCE_ERROR':
            # Use lighter resource configuration
            return await self.create_lightweight_environment(task_id)
```

## Performance Patterns

### 1. Async Workflow Execution
```python
class AsyncWorkflowOptimizer:
    async def optimize_workflow_execution(
        self, 
        workflow_steps: List[WorkflowStep]
    ) -> WorkflowResult:
        """Execute workflow steps with optimal parallelization"""
        
        # Identify parallelizable steps
        parallel_groups = self.identify_parallel_steps(workflow_steps)
        
        # Execute parallel groups
        results = []
        for group in parallel_groups:
            if len(group) == 1:
                # Sequential execution
                result = await self.execute_step(group[0])
                results.append(result)
            else:
                # Parallel execution
                parallel_results = await asyncio.gather(
                    *[self.execute_step(step) for step in group]
                )
                results.extend(parallel_results)
        
        return WorkflowResult(step_results=results)
```

### 2. Caching Strategy
```python
class CodingCacheManager:
    def __init__(self, cache_ttl: int = 3600):
        self.analysis_cache = TTLCache(maxsize=100, ttl=cache_ttl)
        self.code_cache = TTLCache(maxsize=50, ttl=cache_ttl)
        self.test_cache = TTLCache(maxsize=200, ttl=cache_ttl)
    
    async def get_cached_analysis(
        self, 
        requirements_hash: str
    ) -> Optional[AnalysisResult]:
        """Get cached requirement analysis"""
        return self.analysis_cache.get(requirements_hash)
    
    async def cache_code_generation(
        self, 
        plan_hash: str, 
        generated_code: GeneratedCode
    ):
        """Cache generated code for similar plans"""
        self.code_cache[plan_hash] = generated_code
    
    async def get_cached_test_results(
        self, 
        code_hash: str
    ) -> Optional[TestResults]:
        """Get cached test results for identical code"""
        return self.test_cache.get(code_hash)
```

### 3. Resource Management
```python
class ResourceManager:
    def __init__(self, max_concurrent_tasks: int = 3):
        self.semaphore = asyncio.Semaphore(max_concurrent_tasks)
        self.active_environments = {}
        self.resource_monitor = ResourceMonitor()
    
    async def execute_with_resource_control(
        self, 
        task: CodingTask
    ) -> CodingResult:
        """Execute coding task with resource management"""
        async with self.semaphore:
            # Monitor resource usage
            resources = await self.resource_monitor.check_available_resources()
            
            if not resources.sufficient_for_task(task):
                await self.cleanup_unused_environments()
                resources = await self.resource_monitor.check_available_resources()
            
            if resources.sufficient_for_task(task):
                return await self.execute_coding_task(task)
            else:
                raise InsufficientResourcesError(f"Not enough resources for task {task.id}")
```

## Security Patterns

### 1. Sandboxed Execution
```python
class SecureExecutionEnvironment:
    def __init__(self):
        self.container_client = docker.from_env()
        self.security_config = SecurityConfiguration()
    
    async def create_secure_environment(self, task_id: str) -> SecureEnvironment:
        """Create secure, isolated environment for code execution"""
        container = self.container_client.containers.run(
            image="coding-agent-sandbox:latest",
            detach=True,
            network_mode="none",  # No network access
            mem_limit="1g",       # Memory limit
            cpu_period=100000,    # CPU limit
            cpu_quota=50000,      # 50% CPU
            security_opt=["no-new-privileges:true"],  # Security restrictions
            cap_drop=["ALL"],     # Drop all capabilities
            read_only=True,       # Read-only root filesystem
            tmpfs={"/tmp": "size=100m,noexec"}  # Temporary filesystem
        )
        
        return SecureEnvironment(container, task_id)
```

### 2. Code Validation
```python
class CodeSecurityValidator:
    def __init__(self):
        self.security_patterns = self.load_security_patterns()
        self.forbidden_imports = [
            'subprocess', 'os.system', 'eval', 'exec', 
            '__import__', 'open', 'file'
        ]
    
    async def validate_generated_code(self, code: str) -> SecurityValidation:
        """Validate generated code for security issues"""
        issues = []
        
        # Check for dangerous imports
        dangerous_imports = self.check_dangerous_imports(code)
        if dangerous_imports:
            issues.extend(dangerous_imports)
        
        # Check for code injection patterns
        injection_patterns = self.check_injection_patterns(code)
        if injection_patterns:
            issues.extend(injection_patterns)
        
        # Check for file system access
        fs_access = self.check_filesystem_access(code)
        if fs_access:
            issues.extend(fs_access)
        
        return SecurityValidation(
            is_safe=len(issues) == 0,
            security_issues=issues
        )
```

### 3. Git Security
```python
class SecureGitOperations:
    def __init__(self, github_token: str):
        self.github_client = Github(github_token)
        self.allowed_repos = set(settings.ALLOWED_REPOSITORIES)
        self.repo_validator = RepositoryValidator()
    
    async def secure_clone_repository(
        self, 
        repo_url: str, 
        workspace: str
    ) -> SecureRepository:
        """Securely clone repository with validation"""
        
        # Validate repository URL
        if not self.repo_validator.is_allowed_repository(repo_url):
            raise UnauthorizedRepositoryError(repo_url)
        
        # Clone with security restrictions
        repo = git.Repo.clone_from(
            url=repo_url,
            to_path=workspace,
            depth=1,  # Shallow clone
            branch="master"  # Only clone master branch
        )
        
        # Validate repository contents
        await self.validate_repository_safety(repo)
        
        return SecureRepository(repo, workspace)
```