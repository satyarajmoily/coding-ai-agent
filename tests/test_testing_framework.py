"""
Integration tests for the Testing Framework (Phase 1.3).

This module tests the complete testing infrastructure including:
- Docker environment management
- Test execution and result handling
- Integration with the workflow engine
- Resource cleanup and management
"""

import pytest
import asyncio
import os
import tempfile
from datetime import datetime
from unittest.mock import Mock, patch, AsyncMock

from src.coding_agent.services.testing_service import TestingService
from src.coding_agent.services.docker_service import DockerEnvironmentService
from src.coding_agent.models.testing import (
    TestEnvironment, TestSuite, TestType, TestResults,
    EnvironmentStatus, TestEnvironmentRequest
)
from src.coding_agent.core.workflow_engine import WorkflowEngine, WorkflowContext
from src.coding_agent.models.requests import CodingRequest


class TestTestingService:
    """Test the core testing service functionality."""
    
    @pytest.fixture
    def testing_service(self):
        """Create a testing service instance for tests."""
        with patch('docker.from_env'):
            return TestingService()
    
    @pytest.fixture
    def mock_docker_service(self):
        """Create a mock docker service."""
        service = Mock(spec=DockerEnvironmentService)
        service.create_container = AsyncMock()
        service.execute_command = AsyncMock()
        service.cleanup_container = AsyncMock()
        return service
    
    @pytest.mark.asyncio
    async def test_create_test_environment_success(self, testing_service, mock_docker_service):
        """Test successful test environment creation."""
        # Mock successful container creation
        mock_container = Mock()
        mock_container.id = "test_container_123"
        mock_container.name = "coding-agent-test-env"
        mock_container.status = "running"
        
        mock_docker_service.create_container.return_value = mock_container
        testing_service.docker_service = mock_docker_service
        
        # Create test environment
        env = await testing_service.create_test_environment(
            task_id="test_task_123",
            target_service="market-predictor"
        )
        
        # Assertions
        assert env.task_id == "test_task_123"
        assert env.target_service == "market-predictor"
        assert env.container_id == "test_container_123"
        assert env.status == EnvironmentStatus.READY
        assert env.env_id in testing_service.active_environments
    
    @pytest.mark.asyncio
    async def test_create_test_environment_failure(self, testing_service, mock_docker_service):
        """Test test environment creation failure."""
        # Mock container creation failure
        mock_docker_service.create_container.return_value = None
        testing_service.docker_service = mock_docker_service
        
        # Create test environment
        env = await testing_service.create_test_environment(
            task_id="test_task_456",
            target_service="market-predictor"
        )
        
        # Assertions
        assert env.status == EnvironmentStatus.FAILED
        assert env.error_message == "Failed to create Docker container"
    
    @pytest.mark.asyncio
    async def test_install_dependencies_success(self, testing_service, mock_docker_service):
        """Test successful dependency installation."""
        # Create test environment
        env = TestEnvironment(
            env_id="test_env_123",
            task_id="test_task_123",
            container_id="container_123",
            status=EnvironmentStatus.READY
        )
        
        # Mock successful command execution
        mock_result = Mock()
        mock_result.exit_code = 0
        mock_docker_service.execute_command.return_value = mock_result
        testing_service.docker_service = mock_docker_service
        
        # Install dependencies
        success = await testing_service.install_dependencies(env)
        
        # Assertions
        assert success is True
        assert env.dependencies_installed is True
        assert env.status == EnvironmentStatus.READY
    
    @pytest.mark.asyncio
    async def test_install_dependencies_failure(self, testing_service, mock_docker_service):
        """Test dependency installation failure."""
        # Create test environment
        env = TestEnvironment(
            env_id="test_env_456",
            task_id="test_task_456",
            container_id="container_456",
            status=EnvironmentStatus.READY
        )
        
        # Mock failed command execution
        mock_result = Mock()
        mock_result.exit_code = 1
        mock_result.stderr = "Package not found"
        mock_docker_service.execute_command.return_value = mock_result
        testing_service.docker_service = mock_docker_service
        
        # Install dependencies
        success = await testing_service.install_dependencies(env)
        
        # Assertions
        assert success is False
        assert env.status == EnvironmentStatus.FAILED
        assert "Failed to execute" in env.error_message
    
    @pytest.mark.asyncio
    async def test_run_test_suite_success(self, testing_service, mock_docker_service):
        """Test successful test suite execution."""
        # Create test environment
        env = TestEnvironment(
            env_id="test_env_789",
            task_id="test_task_789",
            container_id="container_789",
            status=EnvironmentStatus.READY
        )
        
        # Mock successful test execution
        mock_exec_result = Mock()
        mock_exec_result.exit_code = 0
        mock_exec_result.stdout = "All tests passed"
        
        mock_json_result = Mock()
        mock_json_result.exit_code = 0
        mock_json_result.stdout = '''
        {
            "summary": {"passed": 5, "failed": 0, "skipped": 1},
            "tests": [
                {"nodeid": "test_file.py::test_function", "outcome": "passed", "duration": 0.1}
            ]
        }
        '''
        
        mock_docker_service.execute_command.side_effect = [mock_exec_result, mock_json_result]
        mock_docker_service.write_file_in_container = AsyncMock(return_value=True)
        testing_service.docker_service = mock_docker_service
        
        # Create test suite
        test_suite = TestSuite(
            test_type=TestType.UNIT,
            test_files={"test_example.py": "def test_example(): assert True"},
            timeout_seconds=300
        )
        
        # Run test suite
        results = await testing_service.run_test_suite(env, test_suite)
        
        # Assertions
        assert results.success is True
        assert results.passed == 5
        assert results.failed == 0
        assert results.total == 6  # 5 passed + 1 skipped
        assert len(results.test_details) == 1
    
    @pytest.mark.asyncio
    async def test_cleanup_environment_success(self, testing_service, mock_docker_service):
        """Test successful environment cleanup."""
        # Create test environment
        env = TestEnvironment(
            env_id="test_env_cleanup",
            task_id="test_task_cleanup",
            container_id="container_cleanup",
            workspace_path="/tmp/test_workspace"
        )
        
        # Add to active environments
        testing_service.active_environments[env.env_id] = env
        
        # Mock successful cleanup
        mock_docker_service.cleanup_container.return_value = True
        testing_service.docker_service = mock_docker_service
        
        # Mock workspace directory exists
        with patch('os.path.exists', return_value=True), \
             patch('shutil.rmtree') as mock_rmtree:
            
            # Cleanup environment
            success = await testing_service.cleanup_environment(env)
            
            # Assertions
            assert success is True
            assert env.status == EnvironmentStatus.CLEANED_UP
            assert env.env_id not in testing_service.active_environments
            mock_rmtree.assert_called_once()


class TestDockerEnvironmentService:
    """Test the Docker environment service."""
    
    @pytest.fixture
    def docker_service(self):
        """Create a docker service instance for tests."""
        with patch('docker.from_env') as mock_docker:
            mock_client = Mock()
            mock_docker.return_value = mock_client
            mock_client.ping.return_value = True
            return DockerEnvironmentService()
    
    @pytest.mark.asyncio
    async def test_create_container_success(self, docker_service):
        """Test successful container creation."""
        # Mock container creation
        mock_container = Mock()
        mock_container.id = "container_abc123"
        mock_container.name = "test-container"
        mock_container.status = "running"
        
        docker_service.docker_client.containers.run.return_value = mock_container
        
        # Create container
        container = await docker_service.create_container(
            env_id="test_env_123",
            image="python:3.9-slim"
        )
        
        # Assertions
        assert container is not None
        assert container.id == "container_abc123"
        assert "container_abc123" in docker_service.active_containers
    
    @pytest.mark.asyncio
    async def test_execute_command_success(self, docker_service):
        """Test successful command execution."""
        # Mock container and execution
        mock_container = Mock()
        mock_exec_result = Mock()
        mock_exec_result.exit_code = 0
        mock_exec_result.output = b"Command output"
        mock_container.exec_run.return_value = mock_exec_result
        
        docker_service.docker_client.containers.get.return_value = mock_container
        
        # Execute command
        result = await docker_service.execute_command(
            container_id="container_123",
            command="echo 'test'"
        )
        
        # Assertions
        assert result.exit_code == 0
        assert result.stdout == "Command output"
        assert result.command == "echo 'test'"
    
    @pytest.mark.asyncio
    async def test_execute_command_timeout(self, docker_service):
        """Test command execution timeout."""
        # Mock container that hangs
        mock_container = Mock()
        
        def slow_exec(*args, **kwargs):
            import time
            time.sleep(10)  # Simulate slow command
            
        mock_container.exec_run = slow_exec
        docker_service.docker_client.containers.get.return_value = mock_container
        
        # Execute command with short timeout
        result = await docker_service.execute_command(
            container_id="container_123",
            command="sleep 10",
            timeout=1
        )
        
        # Assertions
        assert result.exit_code == 124  # Timeout exit code
        assert "timed out" in result.stderr.lower()
    
    @pytest.mark.asyncio
    async def test_write_file_in_container(self, docker_service):
        """Test writing file to container."""
        # Mock container
        mock_container = Mock()
        mock_exec_result = Mock()
        mock_exec_result.exit_code = 0
        mock_container.exec_run.return_value = mock_exec_result
        
        docker_service.docker_client.containers.get.return_value = mock_container
        
        # Mock copy_file_to_container method
        docker_service.copy_file_to_container = AsyncMock(return_value=True)
        
        # Write file
        success = await docker_service.write_file_in_container(
            container_id="container_123",
            file_path="/app/test.py",
            content="print('Hello, World!')"
        )
        
        # Assertions
        assert success is True
        docker_service.copy_file_to_container.assert_called_once()


class TestWorkflowIntegration:
    """Test integration with the workflow engine."""
    
    @pytest.fixture
    def workflow_engine(self):
        """Create a workflow engine for testing."""
        with patch('src.coding_agent.agents.coding_agents.CodingAgentOrchestrator'), \
             patch('src.coding_agent.services.code_analysis.CodeAnalysisService'), \
             patch('src.coding_agent.services.git_service.GitService'):
            return WorkflowEngine()
    
    @pytest.mark.asyncio
    async def test_local_testing_integration(self, workflow_engine):
        """Test the local testing step integration."""
        # Create workflow context
        request = CodingRequest(
            requirements="Add a comprehensive test endpoint for status monitoring",
            target_service="market-predictor"
        )
        
        context = WorkflowContext("test_task_integration", request)
        context.workspace_path = "/tmp/test_workspace"
        context.code_changes = []  # No code changes for this test
        
        # Mock testing service
        with patch('src.coding_agent.services.testing_service.TestingService') as mock_service_class:
            mock_service = Mock()
            mock_service_class.return_value = mock_service
            
            # Mock environment creation
            mock_env = Mock()
            mock_env.status = "ready"
            mock_service.create_test_environment = AsyncMock(return_value=mock_env)
            mock_service.install_dependencies = AsyncMock(return_value=True)
            mock_service.start_target_service = AsyncMock(return_value=True)
            mock_service.cleanup_environment = AsyncMock(return_value=True)
            
            # Mock test execution
            mock_results = Mock()
            mock_results.success = True
            mock_results.passed = 3
            mock_results.failed = 0
            mock_results.total = 3
            mock_results.test_details = []
            mock_results.coverage_percentage = 95.0
            mock_service.run_test_suite = AsyncMock(return_value=mock_results)
            
            # Execute local testing step
            next_state = await workflow_engine._handle_local_testing(context)
            
            # Assertions
            assert next_state.value == "validation"
            assert context.statistics.get("testing_completed") is True
            assert context.statistics.get("tests_passed") == 3
            assert context.statistics.get("tests_failed") == 0
            assert context.statistics.get("test_coverage") == 95.0
    
    @pytest.mark.asyncio
    async def test_local_testing_with_failures(self, workflow_engine):
        """Test local testing step with test failures."""
        # Create workflow context
        request = CodingRequest(
            requirements="Add a comprehensive test endpoint with failure scenarios",
            target_service="market-predictor"
        )
        
        context = WorkflowContext("test_task_failures", request)
        context.workspace_path = "/tmp/test_workspace"
        context.code_changes = []
        
        # Mock testing service with failures
        with patch('src.coding_agent.services.testing_service.TestingService') as mock_service_class:
            mock_service = Mock()
            mock_service_class.return_value = mock_service
            
            # Mock environment creation
            mock_env = Mock()
            mock_env.status = "ready"
            mock_service.create_test_environment = AsyncMock(return_value=mock_env)
            mock_service.install_dependencies = AsyncMock(return_value=True)
            mock_service.cleanup_environment = AsyncMock(return_value=True)
            
            # Mock test execution with failures
            mock_results = Mock()
            mock_results.success = False
            mock_results.passed = 2
            mock_results.failed = 1
            mock_results.total = 3
            mock_results.test_details = []
            mock_results.coverage_percentage = 75.0
            mock_service.run_test_suite = AsyncMock(return_value=mock_results)
            
            # Execute local testing step
            next_state = await workflow_engine._handle_local_testing(context)
            
            # Assertions
            assert next_state.value == "validation"  # Should continue despite failures
            assert context.statistics.get("testing_completed") is True
            assert context.statistics.get("tests_passed") == 2
            assert context.statistics.get("tests_failed") == 1
            assert context.statistics.get("test_failures_ignored") is True
    
    @pytest.mark.asyncio
    async def test_local_testing_environment_failure(self, workflow_engine):
        """Test local testing with environment creation failure."""
        # Create workflow context
        request = CodingRequest(
            requirements="Add a comprehensive test endpoint for environment failure testing",
            target_service="market-predictor"
        )
        
        context = WorkflowContext("test_task_env_failure", request)
        
        # Mock testing service with environment failure
        with patch('src.coding_agent.services.testing_service.TestingService') as mock_service_class:
            mock_service = Mock()
            mock_service_class.return_value = mock_service
            
            # Mock environment creation failure
            mock_env = Mock()
            mock_env.status = "failed"
            mock_env.error_message = "Docker not available"
            mock_service.create_test_environment = AsyncMock(return_value=mock_env)
            
            # Execute local testing step
            next_state = await workflow_engine._handle_local_testing(context)
            
            # Assertions
            assert next_state.value == "validation"  # Should continue despite failure
            assert context.statistics.get("testing_failed") is True
            assert "Docker not available" in context.statistics.get("testing_error", "")


class TestEndToEndTestingWorkflow:
    """End-to-end testing workflow tests."""
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_complete_testing_workflow(self):
        """Test complete testing workflow from creation to cleanup."""
        # This test requires Docker to be available
        # Skip if Docker is not available
        try:
            import docker
            client = docker.from_env()
            client.ping()
        except Exception:
            pytest.skip("Docker not available for integration test")
        
        # Create testing service
        testing_service = TestingService()
        
        if not testing_service.docker_service.is_docker_available():
            pytest.skip("Docker service not available")
        
        # Test environment creation
        env = await testing_service.create_test_environment(
            task_id="integration_test_123",
            target_service="test-service"
        )
        
        try:
            assert env.status in [EnvironmentStatus.READY, EnvironmentStatus.CREATING]
            
            # If environment creation succeeded, test dependency installation
            if env.status == EnvironmentStatus.READY:
                deps_success = await testing_service.install_dependencies(
                    env,
                    additional_packages=["pytest"]
                )
                assert deps_success is True
                
                # Test basic test execution
                test_suite = TestSuite(
                    test_type=TestType.UNIT,
                    test_files={
                        "test_basic.py": """
import pytest

def test_basic():
    assert True

def test_addition():
    assert 1 + 1 == 2
"""
                    }
                )
                
                results = await testing_service.run_test_suite(env, test_suite)
                assert results.total >= 2
                assert results.passed >= 2
        
        finally:
            # Always cleanup
            await testing_service.cleanup_environment(env)
    
    def test_generate_basic_test_suite(self):
        """Test basic test suite generation."""
        workflow_engine = WorkflowEngine()
        
        # Create minimal context
        request = CodingRequest(requirements="Test basic functionality with comprehensive validation")
        context = WorkflowContext("test_basic_suite", request)
        
        # Generate test suite
        test_content = workflow_engine._generate_basic_test_suite(context)
        
        # Assertions
        assert "import pytest" in test_content
        assert "def test_implementation_exists" in test_content
        assert "class TestGeneratedCode" in test_content
        assert "Auto-generated by Coding AI Agent" in test_content


# Test configuration
pytest_plugins = ["pytest_asyncio"] 