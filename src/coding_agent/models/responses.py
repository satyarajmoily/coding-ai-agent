"""
Response models for the Coding AI Agent API.

Defines all response models with comprehensive status information
and progress tracking for the autonomous coding workflow.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class TaskStatus(str, Enum):
    """Status values for coding tasks."""
    INITIATED = "initiated"
    ANALYZING = "analyzing"
    PLANNING = "planning"
    CLONING = "cloning"
    CODING = "coding"
    TESTING = "testing"
    VALIDATING = "validating"
    COMMITTING = "committing"
    PR_CREATING = "pr_creating"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class WorkflowStep(BaseModel):
    """Individual step in the coding workflow."""
    
    step_name: str = Field(..., description="Name of the workflow step")
    status: str = Field(..., description="Status of this step")
    started_at: Optional[datetime] = Field(None, description="When this step started")
    completed_at: Optional[datetime] = Field(None, description="When this step completed")
    duration_seconds: Optional[float] = Field(None, description="Duration in seconds")
    error_message: Optional[str] = Field(None, description="Error message if step failed")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional step details")


class CodeChange(BaseModel):
    """Information about a code change made during the workflow."""
    
    file_path: str = Field(..., description="Path of the modified file")
    change_type: str = Field(..., description="Type of change: created, modified, deleted")
    lines_added: int = Field(default=0, description="Number of lines added")
    lines_removed: int = Field(default=0, description="Number of lines removed")
    description: str = Field(..., description="Description of the change")


class TestResult(BaseModel):
    """Result of running tests during the workflow."""
    
    test_file: str = Field(..., description="Path of the test file")
    test_name: str = Field(..., description="Name of the test")
    status: str = Field(..., description="Test status: passed, failed, skipped")
    duration_seconds: float = Field(..., description="Test execution time")
    error_message: Optional[str] = Field(None, description="Error message if test failed")


class ValidationResult(BaseModel):
    """Result of code validation checks."""
    
    check_name: str = Field(..., description="Name of the validation check")
    status: str = Field(..., description="Validation status: passed, failed, warning")
    message: str = Field(..., description="Validation message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional validation details")


class CodingResponse(BaseModel):
    """
    Primary response model for coding operations.
    
    Contains all information about the initiated coding task
    including tracking details and estimated completion time.
    """
    
    task_id: str = Field(..., description="Unique task identifier for tracking")
    status: TaskStatus = Field(..., description="Current status of the coding task")
    branch_name: str = Field(..., description="Git branch name for this implementation")
    
    estimated_duration: str = Field(
        ..., 
        description="Estimated time to completion",
        example="5-10 minutes"
    )
    
    created_at: datetime = Field(..., description="When the task was created")
    updated_at: datetime = Field(..., description="When the task was last updated")
    
    progress_percentage: int = Field(
        default=0,
        description="Overall progress percentage (0-100)",
        ge=0,
        le=100
    )
    
    current_step: str = Field(..., description="Current workflow step")
    
    workflow_steps: List[WorkflowStep] = Field(
        default_factory=list,
        description="List of workflow steps and their status"
    )
    
    pr_url: Optional[str] = Field(None, description="GitHub pull request URL when created")
    
    error_message: Optional[str] = Field(None, description="Error message if task failed")
    
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional task metadata")
    
    class Config:
        schema_extra = {
            "example": {
                "task_id": "task_abc123def",
                "status": "analyzing",
                "branch_name": "status-endpoint-abc123",
                "estimated_duration": "5-8 minutes",
                "created_at": "2025-01-27T10:30:00Z",
                "updated_at": "2025-01-27T10:30:30Z",
                "progress_percentage": 15,
                "current_step": "Analyzing requirements and codebase",
                "workflow_steps": [
                    {
                        "step_name": "Initialize workspace",
                        "status": "completed",
                        "started_at": "2025-01-27T10:30:00Z",
                        "completed_at": "2025-01-27T10:30:15Z",
                        "duration_seconds": 15.0
                    },
                    {
                        "step_name": "Analyze requirements",
                        "status": "in_progress",
                        "started_at": "2025-01-27T10:30:15Z"
                    }
                ]
            }
        }


class TaskStatusResponse(BaseModel):
    """
    Detailed response model for task status queries.
    
    Provides comprehensive information about task progress,
    code changes, test results, and validation status.
    """
    
    task_id: str = Field(..., description="Unique task identifier")
    status: TaskStatus = Field(..., description="Current task status")
    
    created_at: datetime = Field(..., description="Task creation time")
    updated_at: datetime = Field(..., description="Last update time")
    completed_at: Optional[datetime] = Field(None, description="Task completion time")
    
    total_duration_seconds: Optional[float] = Field(None, description="Total execution time")
    
    progress_percentage: int = Field(..., description="Progress percentage (0-100)")
    current_step: str = Field(..., description="Current workflow step")
    
    workflow_steps: List[WorkflowStep] = Field(..., description="All workflow steps")
    
    code_changes: List[CodeChange] = Field(
        default_factory=list,
        description="List of code changes made"
    )
    
    test_results: List[TestResult] = Field(
        default_factory=list,
        description="Test execution results"
    )
    
    validation_results: List[ValidationResult] = Field(
        default_factory=list,
        description="Code validation results"
    )
    
    branch_name: Optional[str] = Field(None, description="Git branch name")
    commit_hash: Optional[str] = Field(None, description="Git commit hash")
    pr_url: Optional[str] = Field(None, description="GitHub pull request URL")
    
    error_message: Optional[str] = Field(None, description="Error message if failed")
    error_details: Optional[Dict[str, Any]] = Field(None, description="Detailed error information")
    
    logs: Optional[List[str]] = Field(None, description="Execution logs (if requested)")
    
    files_modified: Optional[List[str]] = Field(None, description="List of modified files")
    
    statistics: Optional[Dict[str, Any]] = Field(
        None,
        description="Task statistics and metrics"
    )


class HealthResponse(BaseModel):
    """Response model for health check operations."""
    
    status: str = Field(..., description="Overall health status: healthy, degraded, unhealthy")
    timestamp: datetime = Field(..., description="Health check timestamp")
    
    service_info: Dict[str, Any] = Field(..., description="Service information")
    
    dependencies: Dict[str, Any] = Field(
        default_factory=dict,
        description="Status of external dependencies"
    )
    
    metrics: Optional[Dict[str, Any]] = Field(
        None,
        description="Performance metrics (if requested)"
    )
    
    version: str = Field(..., description="Service version")
    
    uptime_seconds: float = Field(..., description="Service uptime in seconds")


class ErrorResponse(BaseModel):
    """Standard error response model."""
    
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    request_id: Optional[str] = Field(None, description="Request identifier for tracking")
    timestamp: datetime = Field(..., description="Error timestamp")
    
    class Config:
        schema_extra = {
            "example": {
                "error": "ValidationError",
                "message": "Requirements are too vague. Please specify what exactly needs to be implemented.",
                "details": {
                    "field": "requirements",
                    "input": "make it better"
                },
                "request_id": "req_xyz789",
                "timestamp": "2025-01-27T10:30:00Z"
            }
        }


class TaskListResponse(BaseModel):
    """Response model for listing tasks."""
    
    tasks: List[TaskStatusResponse] = Field(..., description="List of tasks")
    total_count: int = Field(..., description="Total number of tasks")
    page: int = Field(default=1, description="Current page number")
    page_size: int = Field(default=20, description="Number of tasks per page")
    has_more: bool = Field(..., description="Whether there are more tasks available")