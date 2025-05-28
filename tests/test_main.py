"""
Test suite for the main FastAPI application.

Tests the core API endpoints and basic functionality
of the Coding AI Agent service.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch

from src.coding_agent.main import app
from src.coding_agent.models.requests import CodingRequest


@pytest.fixture
def client():
    """Create a test client for the FastAPI application."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def mock_workflow_engine():
    """Mock workflow engine for testing."""
    mock_engine = Mock()
    with patch('src.coding_agent.main.get_workflow_engine', return_value=mock_engine):
        yield mock_engine


class TestHealthEndpoint:
    """Test the health check endpoint."""
    
    def test_health_check_basic(self, client):
        """Test basic health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] in ["healthy", "degraded", "unhealthy"]
        assert "service_info" in data
        assert "version" in data
        assert "uptime_seconds" in data
    
    def test_health_check_with_dependencies(self, client):
        """Test health check with dependency information."""
        response = client.get("/health?include_dependencies=true")
        assert response.status_code == 200
        
        data = response.json()
        assert "dependencies" in data
    
    def test_health_check_with_metrics(self, client):
        """Test health check with metrics."""
        response = client.get("/health?include_metrics=true")
        assert response.status_code == 200
        
        data = response.json()
        # Metrics might be None if not available
        assert "metrics" in data


class TestRootEndpoint:
    """Test the root service information endpoint."""
    
    def test_root_endpoint(self, client):
        """Test the root endpoint returns service information."""
        response = client.get("/")
        assert response.status_code == 200
        
        data = response.json()
        assert data["service"] == "Coding AI Agent"
        assert "description" in data
        assert "version" in data
        assert "endpoints" in data
        assert "capabilities" in data
        assert "example_request" in data


class TestCodingEndpoint:
    """Test the main coding endpoint."""
    
    def test_coding_endpoint_valid_request(self, client, mock_workflow_engine):
        """Test coding endpoint with valid request."""
        # Mock the workflow engine response
        from src.coding_agent.models.responses import CodingResponse, TaskStatus
        from datetime import datetime
        
        mock_response = CodingResponse(
            task_id="task_abc123def",
            status=TaskStatus.INITIATED,
            branch_name="test-feature-abc123",
            estimated_duration="5-10 minutes",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            progress_percentage=0,
            current_step="Initializing workflow",
            workflow_steps=[]
        )
        
        mock_workflow_engine.start_coding_workflow.return_value = mock_response
        
        # Test request
        request_data = {
            "requirements": "Add a /api/v1/status endpoint that returns current timestamp",
            "target_service": "market-predictor",
            "priority": "medium"
        }
        
        response = client.post("/api/v1/code", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["task_id"] == "task_abc123def"
        assert data["status"] == "initiated"
        assert data["branch_name"] == "test-feature-abc123"
        assert "estimated_duration" in data
    
    def test_coding_endpoint_invalid_requirements(self, client, mock_workflow_engine):
        """Test coding endpoint with invalid requirements."""
        request_data = {
            "requirements": "fix",  # Too vague
            "target_service": "market-predictor"
        }
        
        response = client.post("/api/v1/code", json=request_data)
        assert response.status_code == 422  # Validation error
    
    def test_coding_endpoint_missing_requirements(self, client, mock_workflow_engine):
        """Test coding endpoint with missing requirements."""
        request_data = {
            "target_service": "market-predictor"
        }
        
        response = client.post("/api/v1/code", json=request_data)
        assert response.status_code == 422  # Validation error


class TestTaskStatusEndpoint:
    """Test the task status endpoint."""
    
    def test_task_status_existing_task(self, client, mock_workflow_engine):
        """Test getting status for existing task."""
        from src.coding_agent.models.responses import TaskStatusResponse, TaskStatus
        from datetime import datetime
        
        mock_status = TaskStatusResponse(
            task_id="task_abc123def",
            status=TaskStatus.CODING,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            progress_percentage=60,
            current_step="Generating code implementation",
            workflow_steps=[],
            code_changes=[],
            test_results=[],
            validation_results=[]
        )
        
        mock_workflow_engine.get_task_status.return_value = mock_status
        
        response = client.get("/api/v1/code/task_abc123def/status")
        assert response.status_code == 200
        
        data = response.json()
        assert data["task_id"] == "task_abc123def"
        assert data["status"] == "coding"
        assert data["progress_percentage"] == 60
    
    def test_task_status_nonexistent_task(self, client, mock_workflow_engine):
        """Test getting status for non-existent task."""
        mock_workflow_engine.get_task_status.return_value = None
        
        response = client.get("/api/v1/code/nonexistent_task/status")
        assert response.status_code == 404
    
    def test_task_status_with_parameters(self, client, mock_workflow_engine):
        """Test task status with query parameters."""
        from src.coding_agent.models.responses import TaskStatusResponse, TaskStatus
        from datetime import datetime
        
        mock_status = TaskStatusResponse(
            task_id="task_abc123def",
            status=TaskStatus.COMPLETED,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            progress_percentage=100,
            current_step="Workflow completed successfully",
            workflow_steps=[],
            code_changes=[],
            test_results=[],
            validation_results=[]
        )
        
        mock_workflow_engine.get_task_status.return_value = mock_status
        
        response = client.get("/api/v1/code/task_abc123def/status?include_logs=true&include_files=true")
        assert response.status_code == 200


class TestTaskCancellationEndpoint:
    """Test the task cancellation endpoint."""
    
    def test_cancel_existing_task(self, client, mock_workflow_engine):
        """Test cancelling an existing task."""
        mock_workflow_engine.cancel_task.return_value = True
        
        response = client.delete("/api/v1/code/task_abc123def")
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert "task_abc123def" in data["message"]
    
    def test_cancel_nonexistent_task(self, client, mock_workflow_engine):
        """Test cancelling a non-existent task."""
        mock_workflow_engine.cancel_task.return_value = False
        
        response = client.delete("/api/v1/code/nonexistent_task")
        assert response.status_code == 404


class TestTaskListEndpoint:
    """Test the task listing endpoint."""
    
    def test_list_tasks_empty(self, client, mock_workflow_engine):
        """Test listing tasks when no tasks exist."""
        mock_workflow_engine.active_workflows = {}
        
        response = client.get("/api/v1/tasks")
        assert response.status_code == 200
        
        data = response.json()
        assert data["tasks"] == []
        assert data["total_count"] == 0
        assert data["page"] == 1
    
    def test_list_tasks_with_pagination(self, client, mock_workflow_engine):
        """Test listing tasks with pagination."""
        mock_workflow_engine.active_workflows = {}
        
        response = client.get("/api/v1/tasks?page=1&page_size=10")
        assert response.status_code == 200
        
        data = response.json()
        assert data["page"] == 1
        assert data["page_size"] == 10


class TestRequestValidation:
    """Test request validation logic."""
    
    def test_coding_request_validation(self):
        """Test CodingRequest model validation."""
        # Valid request
        valid_request = CodingRequest(
            requirements="Add a /api/v1/status endpoint that returns current timestamp and uptime",
            target_service="market-predictor",
            priority="medium"
        )
        assert valid_request.requirements is not None
        assert valid_request.target_service == "market-predictor"
        
        # Test validation errors
        with pytest.raises(ValueError):
            CodingRequest(
                requirements="fix",  # Too vague
                target_service="market-predictor"
            )
        
        with pytest.raises(ValueError):
            CodingRequest(
                requirements="make better improve",  # All vague words
                target_service="market-predictor"
            )