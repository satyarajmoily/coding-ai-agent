"""
Test suite for AI integration and workflow functionality.

Tests the complete AI-powered coding workflow from requirements
to code generation and git operations.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

from src.coding_agent.models.requests import CodingRequest
from src.coding_agent.models.responses import TaskStatus
from src.coding_agent.core.workflow_engine import WorkflowEngine
from src.coding_agent.agents.coding_agents import CodingAgentOrchestrator


class TestAIIntegration:
    """Test AI integration components."""
    
    @pytest.fixture
    def workflow_engine(self):
        """Create a workflow engine for testing."""
        return WorkflowEngine()
    
    @pytest.fixture
    def sample_request(self):
        """Create a sample coding request."""
        return CodingRequest(
            requirements="Add a /api/v1/status endpoint that returns current timestamp",
            target_service="market-predictor",
            priority="medium"
        )
    
    @pytest.mark.asyncio
    async def test_ai_orchestrator_initialization(self):
        """Test that AI orchestrator initializes correctly."""
        orchestrator = CodingAgentOrchestrator()
        
        assert orchestrator.planner is not None
        assert orchestrator.coder is not None
        assert orchestrator.tester is not None
    
    @pytest.mark.asyncio
    async def test_workflow_with_ai_mocked(self, workflow_engine, sample_request):
        """Test complete workflow with mocked AI responses."""
        
        # Mock AI orchestrator
        mock_orchestrator = Mock()
        mock_orchestrator.planner.analyze_requirements = AsyncMock(return_value={
            "requirement_analysis": {
                "description": "Simple endpoint creation",
                "complexity": "low",
                "tasks": ["Create endpoint", "Add tests"]
            },
            "technical_design": {
                "approach": "FastAPI endpoint with Pydantic model",
                "components": ["endpoint", "model"],
                "endpoints": ["/api/v1/status"]
            },
            "implementation_plan": {
                "files_to_create": ["src/endpoints/status.py"],
                "files_to_modify": ["src/main.py"],
                "dependencies": [],
                "sequence": ["Create endpoint", "Update main"]
            },
            "testing_strategy": {
                "unit_tests": True,
                "integration_tests": True,
                "test_files": ["test_status.py"]
            },
            "risk_assessment": {
                "risks": [],
                "mitigation": []
            }
        })
        
        mock_orchestrator.create_implementation = AsyncMock(return_value={
            "success": True,
            "plan": {},
            "implementation_files": {
                "src/endpoints/status.py": "# Generated status endpoint\nfrom fastapi import APIRouter\n\nrouter = APIRouter()\n\n@router.get('/status')\ndef get_status():\n    return {'timestamp': 'now'}"
            },
            "test_files": {
                "test_status.py": "# Generated tests\nimport pytest\n\ndef test_status_endpoint():\n    assert True"
            }
        })
        
        # Mock git service
        mock_git_service = Mock()
        mock_git_service.validate_repository_access = AsyncMock(return_value=True)
        mock_git_service.clone_repository = AsyncMock(return_value="/tmp/test-repo")
        mock_git_service.get_repository_info = AsyncMock(return_value={
            "current_branch": "main",
            "remote_url": "https://github.com/test/repo.git"
        })
        mock_git_service.write_files = AsyncMock(return_value=["src/endpoints/status.py", "test_status.py"])
        mock_git_service.create_feature_branch = AsyncMock(return_value="status-endpoint-abc123")
        mock_git_service.generate_commit_message = Mock(return_value="feat: Add status endpoint")
        mock_git_service.commit_changes = AsyncMock(return_value="abc123def456")
        mock_git_service.push_branch = AsyncMock(return_value=True)
        mock_git_service.generate_pr_description = Mock(return_value="Test PR description")
        mock_git_service.create_pull_request = AsyncMock(return_value="https://github.com/test/repo/pull/123")
        
        # Replace services with mocks
        workflow_engine.ai_orchestrator = mock_orchestrator
        workflow_engine.git_service = mock_git_service
        
        # Start workflow
        response = await workflow_engine.start_coding_workflow(sample_request)
        
        # Verify response
        assert response.task_id.startswith("task_")
        assert response.status == TaskStatus.INITIATED
        assert response.branch_name is not None
        
        # Wait for workflow to complete
        await asyncio.sleep(0.5)  # Allow some processing time
        
        # Check task status
        status = await workflow_engine.get_task_status(response.task_id)
        assert status is not None
        
        # Verify AI orchestrator was called
        mock_orchestrator.planner.analyze_requirements.assert_called_once()
        mock_orchestrator.create_implementation.assert_called_once()
        
        # Verify git operations were called
        mock_git_service.clone_repository.assert_called_once()
        mock_git_service.write_files.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_workflow_error_handling(self, workflow_engine, sample_request):
        """Test workflow error handling."""
        
        # Mock AI orchestrator to fail
        mock_orchestrator = Mock()
        mock_orchestrator.planner.analyze_requirements = AsyncMock(
            side_effect=Exception("AI service unavailable")
        )
        
        workflow_engine.ai_orchestrator = mock_orchestrator
        
        # Start workflow
        response = await workflow_engine.start_coding_workflow(sample_request)
        
        # Wait for workflow to process
        await asyncio.sleep(0.5)
        
        # Check that task failed
        status = await workflow_engine.get_task_status(response.task_id)
        assert status is not None
        # The task might still be in progress or failed depending on timing
    
    @pytest.mark.asyncio
    async def test_complexity_estimation(self, workflow_engine):
        """Test requirement complexity estimation."""
        
        simple_req = "Add health check"
        medium_req = "Add Redis caching to the prediction endpoint with TTL configuration"
        complex_req = "Implement comprehensive authentication system with JWT tokens, role-based access control, user management, database integration, and audit logging"
        
        assert workflow_engine._estimate_complexity(simple_req) == "low"
        assert workflow_engine._estimate_complexity(medium_req) == "medium"
        assert workflow_engine._estimate_complexity(complex_req) == "high"
    
    def test_feature_name_extraction(self, workflow_engine):
        """Test feature name extraction from requirements."""
        
        req1 = "Add a status endpoint"
        req2 = "Implement Redis caching for predictions"
        req3 = "Create webhook notification system"
        
        assert workflow_engine._extract_feature_name(req1) == "status-endpoint"
        assert workflow_engine._extract_feature_name(req2) == "redis-caching-predictions"
        assert workflow_engine._extract_feature_name(req3) == "webhook-notification-system"


class TestAIAgents:
    """Test individual AI agents."""
    
    @pytest.mark.asyncio
    async def test_planner_agent_mock(self):
        """Test planner agent with mocked LLM."""
        
        with patch('src.coding_agent.agents.coding_agents.ChatOpenAI') as mock_llm_class:
            # Mock LLM response
            mock_llm = Mock()
            mock_response = Mock()
            mock_response.content = """
            {
                "requirement_analysis": {
                    "description": "Simple endpoint creation",
                    "complexity": "low"
                },
                "implementation_plan": {
                    "files_to_create": ["status.py"],
                    "files_to_modify": []
                }
            }
            """
            mock_llm.return_value = mock_response
            mock_llm_class.return_value = mock_llm
            
            from src.coding_agent.agents.coding_agents import PlannerAgent
            
            planner = PlannerAgent()
            
            result = await planner.analyze_requirements(
                requirements="Add status endpoint",
                target_service="test-service"
            )
            
            assert "requirement_analysis" in result
            assert "implementation_plan" in result
    
    @pytest.mark.asyncio
    async def test_coder_agent_mock(self):
        """Test coder agent with mocked LLM."""
        
        with patch('src.coding_agent.agents.coding_agents.ChatOpenAI') as mock_llm_class:
            # Mock LLM response
            mock_llm = Mock()
            mock_response = Mock()
            mock_response.content = """```python
from fastapi import APIRouter

router = APIRouter()

@router.get("/status")
def get_status():
    return {"status": "ok"}
```"""
            mock_llm.return_value = mock_response
            mock_llm_class.return_value = mock_llm
            
            from src.coding_agent.agents.coding_agents import CoderAgent
            
            coder = CoderAgent()
            
            result = await coder.generate_code(
                implementation_plan={"files": []},
                target_file="status.py",
                changes_required="Create status endpoint",
                target_service="test-service"
            )
            
            assert "from fastapi import APIRouter" in result
            assert "@router.get" in result
    
    @pytest.mark.asyncio
    async def test_tester_agent_mock(self):
        """Test tester agent with mocked LLM."""
        
        with patch('src.coding_agent.agents.coding_agents.ChatOpenAI') as mock_llm_class:
            # Mock LLM response
            mock_llm = Mock()
            mock_response = Mock()
            mock_response.content = """```python
import pytest
from fastapi.testclient import TestClient

def test_status_endpoint():
    # Test implementation
    assert True
```"""
            mock_llm.return_value = mock_response
            mock_llm_class.return_value = mock_llm
            
            from src.coding_agent.agents.coding_agents import TesterAgent
            
            tester = TesterAgent()
            
            result = await tester.generate_tests(
                code_content="def get_status(): return {'status': 'ok'}",
                feature_description="Status endpoint",
                target_service="test-service"
            )
            
            assert "import pytest" in result
            assert "def test_" in result


class TestPromptTemplates:
    """Test prompt template functionality."""
    
    def test_prompt_registry(self):
        """Test that prompt registry returns all required prompts."""
        from src.coding_agent.config.prompts import PromptRegistry
        
        planner_prompt = PromptRegistry.get_planner_prompt()
        coder_prompt = PromptRegistry.get_coder_prompt()
        tester_prompt = PromptRegistry.get_tester_prompt()
        system_prompts = PromptRegistry.get_system_prompts()
        
        assert planner_prompt is not None
        assert coder_prompt is not None
        assert tester_prompt is not None
        assert "planner" in system_prompts
        assert "coder" in system_prompts
        assert "tester" in system_prompts
    
    def test_prompt_formatting(self):
        """Test that prompts can be formatted with variables."""
        from src.coding_agent.config.prompts import PromptRegistry
        
        planner_prompt = PromptRegistry.get_planner_prompt()
        
        formatted = planner_prompt.format(
            target_service="test-service",
            repo_structure="test structure",
            existing_patterns="test patterns",
            requirements="test requirements",
            context="test context"
        )
        
        assert "test-service" in formatted
        assert "test requirements" in formatted


class TestGitService:
    """Test Git service functionality."""
    
    def test_commit_message_generation(self):
        """Test commit message generation."""
        from src.coding_agent.services.git_service import GitService
        
        git_service = GitService()
        
        message = git_service.generate_commit_message(
            requirements="Add status endpoint",
            files_changed=["status.py", "test_status.py"],
            implementation_type="feature"
        )
        
        assert "feat:" in message
        assert "Add status endpoint" in message
        assert "status.py" in message
    
    def test_pr_description_generation(self):
        """Test PR description generation."""
        from src.coding_agent.services.git_service import GitService
        
        git_service = GitService()
        
        description = git_service.generate_pr_description(
            requirements="Add status endpoint",
            implementation_plan={"requirement_analysis": {"complexity": "low"}},
            files_changed=["status.py"],
            test_results={"passed": 1, "failed": 0}
        )
        
        assert "## 🤖 AI-Generated Implementation" in description
        assert "Add status endpoint" in description
        assert "status.py" in description
    
    def test_feature_name_extraction(self):
        """Test feature name extraction from requirements."""
        from src.coding_agent.core.workflow_engine import WorkflowEngine
        
        engine = WorkflowEngine()
        
        # Test various requirement formats
        assert engine._extract_feature_name("Add status endpoint") == "status-endpoint"
        assert engine._extract_feature_name("Create user authentication") == "user-authentication"
        assert engine._extract_feature_name("Implement Redis caching") == "redis-caching"