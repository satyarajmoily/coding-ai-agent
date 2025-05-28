"""
Testing Models - Data models for the testing framework.

This module defines all data structures used in the testing infrastructure:
- Test environments and their lifecycle
- Test execution results and details
- Container management data
- Test suite configurations
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field


class EnvironmentStatus(str, Enum):
    """Status of a test environment."""
    CREATING = "creating"
    READY = "ready"
    INSTALLING_DEPS = "installing_deps"
    STARTING_SERVICE = "starting_service"
    SERVICE_RUNNING = "service_running"
    RUNNING_TESTS = "running_tests"
    FAILED = "failed"
    CLEANED_UP = "cleaned_up"


class TestType(str, Enum):
    """Types of tests that can be executed."""
    UNIT = "unit"
    INTEGRATION = "integration"
    API = "api"
    ALL = "all"


class TestEnvironment(BaseModel):
    """
    Represents a test environment for isolated code validation.
    
    This model tracks the complete lifecycle of a testing environment
    from creation through cleanup.
    """
    
    env_id: str = Field(..., description="Unique environment identifier")
    task_id: str = Field(..., description="Associated task identifier")
    container_id: Optional[str] = Field(default=None, description="Docker container ID")
    status: EnvironmentStatus = Field(default=EnvironmentStatus.CREATING, description="Current environment status")
    
    # Environment configuration
    target_service: str = Field(default="market-predictor", description="Target service for testing")
    python_version: str = Field(default="3.9", description="Python version")
    workspace_path: Optional[str] = Field(default=None, description="Host workspace path")
    
    # Runtime information
    container_info: Optional[Dict[str, Any]] = Field(default=None, description="Container runtime information")
    service_port: Optional[int] = Field(default=None, description="Service port if running")
    dependencies_installed: bool = Field(default=False, description="Whether dependencies are installed")
    service_started: bool = Field(default=False, description="Whether target service is running")
    
    # Lifecycle tracking
    created_at: Optional[datetime] = Field(default=None, description="Environment creation time")
    updated_at: Optional[datetime] = Field(default=None, description="Last update time")
    
    # Error handling
    error_message: Optional[str] = Field(default=None, description="Error message if failed")
    error_details: Optional[Dict[str, Any]] = Field(default=None, description="Detailed error information")
    
    class Config:
        json_schema_extra = {
            "example": {
                "env_id": "test-env-task_abc123-def456",
                "task_id": "task_abc123",
                "container_id": "container_xyz789",
                "status": "ready",
                "target_service": "market-predictor",
                "python_version": "3.9",
                "dependencies_installed": True,
                "service_started": False
            }
        }


class TestDetail(BaseModel):
    """Details of an individual test execution."""
    
    test_name: str = Field(..., description="Name of the test")
    status: str = Field(..., description="Test result status")
    duration_seconds: float = Field(default=0, description="Test execution time")
    error_message: Optional[str] = Field(default=None, description="Error message if failed")
    output: Optional[str] = Field(default=None, description="Test output")
    
    class Config:
        json_schema_extra = {
            "example": {
                "test_name": "test_api_endpoint_status",
                "status": "passed",
                "duration_seconds": 0.234,
                "error_message": None
            }
        }


class TestResults(BaseModel):
    """
    Results of test execution in an environment.
    
    This model contains comprehensive information about test execution
    including individual test results and overall statistics.
    """
    
    test_type: TestType = Field(..., description="Type of tests executed")
    environment_id: str = Field(..., description="Environment where tests ran")
    
    # Test statistics
    passed: int = Field(default=0, description="Number of passed tests")
    failed: int = Field(default=0, description="Number of failed tests")
    skipped: int = Field(default=0, description="Number of skipped tests")
    total: int = Field(default=0, description="Total number of tests")
    
    # Test quality metrics
    coverage_percentage: Optional[float] = Field(default=None, description="Code coverage percentage")
    success: bool = Field(default=False, description="Overall test success")
    
    # Execution timing
    started_at: Optional[datetime] = Field(default=None, description="Test execution start time")
    completed_at: Optional[datetime] = Field(default=None, description="Test execution completion time")
    execution_time: Optional[float] = Field(default=None, description="Total execution time in seconds")
    
    # Detailed results
    test_details: List[TestDetail] = Field(default_factory=list, description="Individual test results")
    
    # Error handling
    error_message: Optional[str] = Field(default=None, description="Error message if execution failed")
    error_details: Optional[Dict[str, Any]] = Field(default=None, description="Detailed error information")
    
    # Additional metadata
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional test metadata")
    
    class Config:
        json_schema_extra = {
            "example": {
                "test_type": "unit",
                "environment_id": "test-env-task_abc123-def456",
                "passed": 8,
                "failed": 0,
                "skipped": 1,
                "total": 9,
                "coverage_percentage": 95.5,
                "success": True,
                "execution_time": 12.34
            }
        }


class TestSuite(BaseModel):
    """
    Configuration for a test suite execution.
    
    This model defines what tests to run and how to run them
    in a test environment.
    """
    
    test_type: TestType = Field(..., description="Type of test suite")
    test_files: Dict[str, str] = Field(..., description="Test files with their content")
    source_files: Optional[Dict[str, str]] = Field(default=None, description="Source files to test")
    
    # Test configuration
    pytest_args: List[str] = Field(default_factory=list, description="Additional pytest arguments")
    timeout_seconds: int = Field(default=300, description="Test execution timeout")
    coverage_threshold: float = Field(default=80.0, description="Minimum coverage threshold")
    
    # Environment requirements
    python_packages: Optional[List[str]] = Field(default=None, description="Additional Python packages required")
    environment_variables: Optional[Dict[str, str]] = Field(default=None, description="Environment variables for tests")
    
    class Config:
        json_schema_extra = {
            "example": {
                "test_type": "unit",
                "test_files": {
                    "test_api.py": "import pytest\n\ndef test_endpoint():\n    assert True"
                },
                "pytest_args": ["-v", "--tb=short"],
                "timeout_seconds": 300,
                "coverage_threshold": 85.0
            }
        }


class CommandResult(BaseModel):
    """Result of a command execution in a container."""
    
    exit_code: int = Field(..., description="Command exit code")
    stdout: str = Field(default="", description="Standard output")
    stderr: str = Field(default="", description="Standard error")
    command: str = Field(..., description="Executed command")
    duration_seconds: float = Field(default=0, description="Command execution time")
    
    # Additional result information
    success: Optional[bool] = Field(default=None, description="Whether command was successful")
    error: Optional[str] = Field(default=None, description="Error message if failed")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional command metadata")
    
    class Config:
        json_schema_extra = {
            "example": {
                "exit_code": 0,
                "stdout": "All tests passed",
                "stderr": "",
                "command": "pytest tests/",
                "duration_seconds": 5.23,
                "success": True
            }
        }


class ContainerInfo(BaseModel):
    """Information about a Docker container."""
    
    container_id: str = Field(..., description="Docker container ID")
    env_id: str = Field(..., description="Associated environment ID")
    name: str = Field(..., description="Container name")
    image: str = Field(..., description="Docker image used")
    status: str = Field(..., description="Container status")
    
    # Container configuration
    workspace_path: Optional[str] = Field(default=None, description="Host workspace path mounted")
    ports: Optional[Dict[str, int]] = Field(default=None, description="Port mappings")
    environment_vars: Optional[Dict[str, str]] = Field(default=None, description="Environment variables")
    
    # Lifecycle tracking
    created_at: Optional[datetime] = Field(default=None, description="Container creation time")
    started_at: Optional[datetime] = Field(default=None, description="Container start time")
    
    # Resource usage
    memory_limit: Optional[str] = Field(default=None, description="Memory limit")
    cpu_limit: Optional[int] = Field(default=None, description="CPU limit")
    
    class Config:
        json_schema_extra = {
            "example": {
                "container_id": "container_xyz789",
                "env_id": "test-env-task_abc123-def456",
                "name": "coding-agent-test-env-xyz",
                "image": "python:3.9-slim",
                "status": "running",
                "memory_limit": "1g",
                "cpu_limit": 1
            }
        }


class TestEnvironmentRequest(BaseModel):
    """Request to create a test environment."""
    
    task_id: str = Field(..., description="Associated task ID")
    target_service: str = Field(default="market-predictor", description="Target service")
    python_version: str = Field(default="3.9", description="Python version")
    requirements_file: Optional[str] = Field(default=None, description="Path to requirements.txt")
    additional_packages: Optional[List[str]] = Field(default=None, description="Additional packages")
    
    class Config:
        json_schema_extra = {
            "example": {
                "task_id": "task_abc123",
                "target_service": "market-predictor",
                "python_version": "3.9",
                "additional_packages": ["redis", "celery"]
            }
        }


class TestExecutionRequest(BaseModel):
    """Request to execute tests in an environment."""
    
    environment_id: str = Field(..., description="Environment ID")
    test_suite: TestSuite = Field(..., description="Test suite to execute")
    
    class Config:
        json_schema_extra = {
            "example": {
                "environment_id": "test-env-task_abc123-def456",
                "test_suite": {
                    "test_type": "unit",
                    "test_files": {
                        "test_api.py": "test content"
                    }
                }
            }
        }


class TestingServiceStatus(BaseModel):
    """Status of the testing service."""
    
    active_environments: int = Field(..., description="Number of active environments")
    active_containers: int = Field(..., description="Number of active containers")
    total_tests_run: int = Field(default=0, description="Total tests executed")
    success_rate: float = Field(default=0.0, description="Overall test success rate")
    
    # Service health
    docker_available: bool = Field(..., description="Whether Docker is available")
    service_healthy: bool = Field(..., description="Overall service health")
    
    # Resource usage
    memory_usage: Optional[str] = Field(default=None, description="Memory usage")
    disk_usage: Optional[str] = Field(default=None, description="Disk usage")
    
    class Config:
        json_schema_extra = {
            "example": {
                "active_environments": 3,
                "active_containers": 3,
                "total_tests_run": 156,
                "success_rate": 94.2,
                "docker_available": True,
                "service_healthy": True
            }
        } 