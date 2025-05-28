"""
Request models for the Coding AI Agent API.

Defines all request models with validation and documentation
for the autonomous coding workflow endpoints.
"""

from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, validator
from enum import Enum


class Priority(str, Enum):
    """Priority levels for coding requests."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TargetService(str, Enum):
    """Supported target services for code modifications."""
    MARKET_PREDICTOR = "market-predictor"
    DEVOPS_AI_AGENT = "devops-ai-agent"
    CODING_AI_AGENT = "coding-ai-agent"


class CodingRequest(BaseModel):
    """
    Primary request model for coding operations.
    
    This model represents a natural language coding requirement
    that will be processed by the AI agent and converted into
    working code with tests and documentation.
    """
    
    requirements: str = Field(
        ...,
        description="Natural language description of what code to implement",
        min_length=10,
        max_length=2000,
        example="Add a /api/v1/status endpoint that returns current timestamp and service uptime"
    )
    
    priority: Priority = Field(
        default=Priority.MEDIUM,
        description="Priority level for this coding request"
    )
    
    target_service: TargetService = Field(
        default=TargetService.MARKET_PREDICTOR,
        description="Target service where code should be implemented"
    )
    
    context: Optional[str] = Field(
        default=None,
        description="Additional context or constraints for the implementation",
        max_length=1000,
        example="This endpoint will be used by monitoring systems, ensure it's fast and reliable"
    )
    
    default_branch: str = Field(
        default="main",
        description="Default branch name to create PR against",
        max_length=100,
        pattern=r"^[a-zA-Z0-9-_/]+$",
        example="main"
    )
    
    skip_tests: bool = Field(
        default=False,
        description="Skip test generation (not recommended for production)"
    )
    
    dry_run: bool = Field(
        default=False,
        description="Perform analysis and planning only, don't execute changes"
    )
    
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional metadata for the request"
    )
    
    @validator("requirements")
    def validate_requirements(cls, v):
        """Validate requirements are meaningful and not too vague."""
        v = v.strip()
        
        # Check for overly vague requirements
        vague_indicators = [
            "make better", "improve", "faster", "optimize", 
            "fix", "enhance", "update", "modify"
        ]
        
        words = v.lower().split()
        if len(words) < 5:
            raise ValueError("Requirements must be more specific (at least 5 words)")
        
        # If it's only vague words, reject it
        if all(word in vague_indicators for word in words if len(word) > 3):
            raise ValueError(
                "Requirements are too vague. Please specify what exactly needs to be implemented."
            )
        
        return v
    
    @validator("context")
    def validate_context(cls, v):
        """Validate context if provided."""
        if v is not None:
            v = v.strip()
            if len(v) < 10:
                raise ValueError("Context should be meaningful if provided")
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "default_branch": "master",
                "context": "This endpoint will be used to add two numbers",
                "dry_run": False,
                "priority": "medium",
                "requirements": "Add a /api/v1/add endpoint that returns current timestamp, and the result of adding any two numbers",
                "skip_tests": False,
                "target_service": "market-predictor"
            }
        }


class TaskStatusRequest(BaseModel):
    """Request model for checking task status."""
    
    task_id: str = Field(
        ...,
        description="Unique task identifier",
        pattern=r"^task_[a-zA-Z0-9]{8,}$"
    )
    
    include_logs: bool = Field(
        default=False,
        description="Include detailed execution logs in response"
    )
    
    include_files: bool = Field(
        default=False,
        description="Include list of modified files in response"
    )


class TaskCancelRequest(BaseModel):
    """Request model for canceling a running task."""
    
    task_id: str = Field(
        ...,
        description="Unique task identifier",
        pattern=r"^task_[a-zA-Z0-9]{8,}$"
    )
    
    reason: Optional[str] = Field(
        default=None,
        description="Reason for cancellation",
        max_length=200
    )
    
    force: bool = Field(
        default=False,
        description="Force cancellation even if task is in critical phase"
    )


class HealthCheckRequest(BaseModel):
    """Request model for health check operations."""
    
    include_dependencies: bool = Field(
        default=True,
        description="Include status of external dependencies"
    )
    
    include_metrics: bool = Field(
        default=False,
        description="Include performance metrics"
    )
    
    timeout: int = Field(
        default=30,
        description="Timeout for dependency checks in seconds",
        ge=5,
        le=120
    )