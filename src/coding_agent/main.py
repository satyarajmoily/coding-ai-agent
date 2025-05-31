"""
Coding AI Agent - Main FastAPI Application

The autonomous software engineer that converts natural language requirements
into production-ready code with tests and documentation.

This service provides:
- Natural language to code conversion
- Complete developer workflow automation
- Git operations and GitHub integration
- Quality assurance and testing
- Progress tracking and status monitoring
"""

import logging
import sys
from datetime import datetime
from typing import Optional, List

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from contextlib import asynccontextmanager
import uvicorn

from .config.settings import get_settings, validate_settings
from .models.requests import CodingRequest, TaskStatusRequest, HealthCheckRequest
from .models.responses import (
    CodingResponse, TaskStatusResponse, HealthResponse, 
    ErrorResponse, TaskListResponse
)
from .core.workflow_engine import WorkflowEngine

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('coding-agent.log') if get_settings().environment != "development" else logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Global instances
workflow_engine: Optional[WorkflowEngine] = None
app_start_time: Optional[datetime] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan management.
    
    Handles startup and shutdown procedures for the Coding AI Agent.
    """
    global workflow_engine, app_start_time
    
    logger.info("🤖 Starting Coding AI Agent - Autonomous Software Engineer")
    
    try:
        # Get settings first
        settings = get_settings()
        
        # Check for required environment variables
        missing_vars = settings.validate_required_settings()
        if missing_vars:
            logger.warning(f"Missing environment variables: {', '.join(missing_vars)}")
            logger.warning("Some features may not work properly without proper configuration")
        
        # Initialize workflow engine
        workflow_engine = WorkflowEngine()
        app_start_time = datetime.utcnow()
        
        logger.info(f"✅ Coding AI Agent started successfully on {settings.api_host}:{settings.api_port}")
        logger.info(f"🔧 LLM provider: {settings.llm_provider} ({settings.llm_model})")
        
        yield
        
    except Exception as e:
        logger.error(f"❌ Failed to start Coding AI Agent: {str(e)}")
        raise
    
    finally:
        # Cleanup
        logger.info("🛑 Shutting down Coding AI Agent")
        if workflow_engine:
            # TODO: Add graceful shutdown of active workflows
            pass


def get_workflow_engine() -> WorkflowEngine:
    """Dependency to get the workflow engine instance."""
    if workflow_engine is None:
        raise HTTPException(status_code=503, detail="Workflow engine not initialized")
    return workflow_engine


# Create FastAPI application
app = FastAPI(
    title="Coding AI Agent",
    description="""
    ## 🤖 Autonomous Software Engineer
    
    The Coding AI Agent is a revolutionary AI-powered system that converts natural language requirements 
    into production-ready code with complete developer workflow automation.
    
    ### 🚀 Key Features:
    - **Natural Language Programming**: Convert requirements directly into working code
    - **Complete Workflow Automation**: Clone → Analyze → Plan → Code → Test → PR
    - **Quality Assurance**: Automated testing and code quality validation
    - **Git Integration**: Automatic branching, committing, and pull request creation
    - **Progress Tracking**: Real-time status monitoring and detailed progress reports
    
    ### 🎯 How It Works:
    1. Submit coding requirements in natural language via `/api/v1/code`
    2. AI analyzes requirements and creates implementation plan
    3. System clones repository and sets up isolated testing environment
    4. AI generates production-quality code with tests
    5. Code is tested locally and validated for quality
    6. Changes are committed to a new branch with unique naming
    7. GitHub pull request is created with detailed description
    
    ### 📊 Example Usage:
    ```json
    {
        "requirements": "Add a /api/v1/status endpoint that returns current timestamp and uptime",
        "target_service": "market-predictor",
        "priority": "medium"
    }
    ```
    
    The AI will create working code, tests, and a pull request in minutes!
    """,
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for better error responses."""
    logger.error(f"Unhandled exception in {request.url}: {str(exc)}")
    
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="InternalServerError",
            message="An unexpected error occurred. Please try again or contact support.",
            details={"url": str(request.url)},
            timestamp=datetime.utcnow()
        ).dict()
    )


@app.get("/", 
    summary="Service Information",
    description="Get basic information about the Coding AI Agent service"
)
async def root():
    """Get service information and available endpoints."""
    return {
        "service": "Coding AI Agent",
        "description": "Autonomous Software Engineer - AI-powered code generation and workflow automation",
        "version": "1.0.0",
        "status": "operational",
        "endpoints": {
            "coding": "/api/v1/code",
            "status": "/api/v1/code/{task_id}/status",
            "health": "/health",
            "metrics": "/metrics",
            "docs": "/docs"
        },
        "capabilities": [
            "Natural language to code conversion",
            "Complete developer workflow automation", 
            "Git operations and GitHub integration",
            "Automated testing and quality assurance",
            "Real-time progress tracking"
        ],
        "example_request": {
            "requirements": "Add a /api/v1/status endpoint that returns current timestamp",
            "target_service": "market-predictor",
            "priority": "medium"
        }
    }


@app.get("/health",
    response_model=HealthResponse,
    summary="Health Check",
    description="Check the health status of the Coding AI Agent and its dependencies"
)
async def health_check(request: HealthCheckRequest = Depends()):
    """
    Comprehensive health check for the Coding AI Agent.
    
    Returns detailed health information including:
    - Service status and uptime
    - External dependency status (if requested)
    - Performance metrics (if requested)
    - Configuration validation
    """
    global app_start_time
    
    settings = get_settings()
    current_time = datetime.utcnow()
    uptime = (current_time - app_start_time).total_seconds() if app_start_time else 0
    
    # Basic service info
    service_info = {
        "name": "Coding AI Agent",
        "version": "1.0.0",
        "environment": settings.environment,
        "start_time": app_start_time.isoformat() if app_start_time else None,
        "uptime_seconds": uptime
    }
    
    # Check dependencies if requested
    dependencies = {}
    overall_status = "healthy"
    
    if request.include_dependencies:
        # Check LLM provider
        if settings.llm_provider == "openai" and settings.openai_api_key:
            dependencies["openai"] = {"status": "configured", "model": settings.llm_model}
        elif settings.llm_provider == "anthropic" and settings.anthropic_api_key:
            dependencies["anthropic"] = {"status": "configured", "model": settings.llm_model}
        else:
            dependencies["llm"] = {"status": "not_configured", "error": "Missing API key"}
            overall_status = "degraded"
        
        # Check GitHub configuration
        if settings.github_token:
            dependencies["github"] = {"status": "configured", "note": "repositories are dynamic per request"}
        else:
            dependencies["github"] = {"status": "not_configured", "error": "Missing GitHub token"}
            overall_status = "degraded"
        
        # Check workspace
        try:
            import os
            workspace_exists = os.path.exists(settings.workspace_base_path)
            dependencies["workspace"] = {
                "status": "available" if workspace_exists else "needs_creation",
                "path": settings.workspace_base_path
            }
        except Exception as e:
            dependencies["workspace"] = {"status": "error", "error": str(e)}
            overall_status = "degraded"
    
    # Include metrics if requested
    metrics = None
    if request.include_metrics:
        metrics = {
            "active_workflows": len(workflow_engine.active_workflows) if workflow_engine else 0,
            "uptime_seconds": uptime,
            "memory_usage": "unknown",  # TODO: Add actual memory monitoring
            "cpu_usage": "unknown"     # TODO: Add actual CPU monitoring
        }
    
    return HealthResponse(
        status=overall_status,
        timestamp=current_time,
        service_info=service_info,
        dependencies=dependencies,
        metrics=metrics,
        version="1.0.0",
        uptime_seconds=uptime
    )


@app.get("/metrics",
    summary="Prometheus Metrics",
    description="Prometheus metrics endpoint for service monitoring",
    response_class=Response,
    tags=["monitoring"]
)
async def get_metrics():
    """
    Prometheus metrics endpoint.
    Returns service health and basic metrics in Prometheus format.
    """
    global app_start_time
    
    current_time = datetime.utcnow()
    uptime = (current_time - app_start_time).total_seconds() if app_start_time else 0
    active_workflows = len(workflow_engine.active_workflows) if workflow_engine else 0
    
    # Prometheus format metrics
    metrics = [
        "# HELP up Service availability (1 = up, 0 = down)",
        "# TYPE up gauge",
        "up 1",
        "",
        "# HELP coding_agent_uptime_seconds Service uptime in seconds",
        "# TYPE coding_agent_uptime_seconds counter",
        f"coding_agent_uptime_seconds {uptime}",
        "",
        "# HELP coding_agent_active_workflows Number of active coding workflows",
        "# TYPE coding_agent_active_workflows gauge", 
        f"coding_agent_active_workflows {active_workflows}",
        "",
        "# HELP coding_agent_info Service information",
        "# TYPE coding_agent_info gauge",
        'coding_agent_info{version="1.0.0",service="coding-ai-agent"} 1',
        ""
    ]
    
    return Response(content="\n".join(metrics), media_type="text/plain")


@app.post("/api/v1/code",
    response_model=CodingResponse,
    summary="Generate Code",
    description="Submit coding requirements and start autonomous development workflow"
)
async def generate_code(
    request: CodingRequest,
    engine: WorkflowEngine = Depends(get_workflow_engine)
) -> CodingResponse:
    """
    🚀 **Main Coding Endpoint - Transform Requirements into Code**
    
    This is the core endpoint of the Coding AI Agent. Submit natural language requirements
    and the AI will automatically:
    
    1. **Analyze** your requirements and the target codebase
    2. **Plan** the implementation with file-level changes
    3. **Generate** production-quality code following best practices
    4. **Test** the implementation in an isolated environment
    5. **Validate** code quality and ensure no regressions
    6. **Commit** changes to a new git branch
    7. **Create** a GitHub pull request with detailed description
    
    ### ⏱️ **Typical Timeline:**
    - Simple endpoints: 3-5 minutes
    - Complex features: 8-15 minutes
    - Integration work: 10-20 minutes
    
    ### 🎯 **Example Requirements:**
    - "Add a /api/v1/status endpoint that returns current timestamp"
    - "Add Redis caching to the prediction endpoint with TTL configuration"
    - "Add input validation with proper error messages"
    
    ### 📊 **Response:**
    Returns a task ID for tracking progress. Use `/api/v1/code/{task_id}/status` 
    to monitor progress and get the GitHub PR URL when completed.
    """
    try:
        logger.info(f"🚀 Starting coding workflow for requirements: {request.requirements[:100]}...")
        
        # Start the workflow
        response = await engine.start_coding_workflow(request)
        
        logger.info(f"✅ Workflow {response.task_id} initiated successfully")
        
        return response
        
    except ValueError as e:
        logger.warning(f"Invalid request: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=ErrorResponse(
                error="ValidationError",
                message=str(e),
                timestamp=datetime.utcnow()
            ).dict()
        )
    except Exception as e:
        logger.error(f"Failed to start coding workflow: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                error="WorkflowError",
                message="Failed to start coding workflow. Please try again.",
                details={"error": str(e)},
                timestamp=datetime.utcnow()
            ).dict()
        )


@app.get("/api/v1/code/{task_id}/status",
    response_model=TaskStatusResponse,
    summary="Get Task Status",
    description="Get detailed status and progress information for a coding task"
)
async def get_task_status(
    task_id: str,
    include_logs: bool = False,
    include_files: bool = False,
    engine: WorkflowEngine = Depends(get_workflow_engine)
) -> TaskStatusResponse:
    """
    📊 **Get Detailed Task Status and Progress**
    
    Monitor the progress of your coding task with comprehensive status information:
    
    ### 📈 **Progress Tracking:**
    - Real-time progress percentage (0-100%)
    - Current workflow step description
    - Detailed timeline of all completed steps
    
    ### 🔍 **Detailed Information:**
    - **Code Changes**: List of files modified with change descriptions
    - **Test Results**: All test execution results with pass/fail status
    - **Validation Results**: Code quality checks and validation status
    - **Git Information**: Branch name, commit hash, and PR URL
    
    ### 📝 **Workflow Steps:**
    1. Initialize workspace
    2. Analyze requirements and codebase
    3. Create implementation plan
    4. Set up development environment
    5. Clone target repository
    6. Generate code implementation
    7. Run local tests
    8. Validate implementation
    9. Commit changes to git
    10. Create GitHub pull request
    11. Clean up resources
    
    ### ✅ **Completion:**
    When status shows "completed", the `pr_url` field will contain the GitHub pull request URL
    ready for review and merging.
    """
    try:
        status = await engine.get_task_status(task_id)
        
        if not status:
            raise HTTPException(
                status_code=404,
                detail=ErrorResponse(
                    error="TaskNotFound",
                    message=f"Task with ID '{task_id}' not found",
                    timestamp=datetime.utcnow()
                ).dict()
            )
        
        # TODO: Add logs and files if requested in future phases
        
        return status
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get task status for {task_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                error="StatusError",
                message="Failed to retrieve task status",
                details={"task_id": task_id, "error": str(e)},
                timestamp=datetime.utcnow()
            ).dict()
        )


@app.delete("/api/v1/code/{task_id}",
    summary="Cancel Task",
    description="Cancel a running coding task"
)
async def cancel_task(
    task_id: str,
    reason: Optional[str] = None,
    engine: WorkflowEngine = Depends(get_workflow_engine)
):
    """
    🛑 **Cancel Running Task**
    
    Cancel a coding task that is currently in progress. This will:
    
    - Stop the current workflow execution
    - Clean up any temporary resources
    - Mark the task as cancelled
    
    **Note:** Tasks that have already completed cannot be cancelled.
    """
    try:
        success = await engine.cancel_task(task_id, reason)
        
        if not success:
            raise HTTPException(
                status_code=404,
                detail=ErrorResponse(
                    error="TaskNotFound",
                    message=f"Task with ID '{task_id}' not found or already completed",
                    timestamp=datetime.utcnow()
                ).dict()
            )
        
        return {"message": f"Task {task_id} cancelled successfully", "reason": reason}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to cancel task {task_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                error="CancellationError",
                message="Failed to cancel task",
                details={"task_id": task_id, "error": str(e)},
                timestamp=datetime.utcnow()
            ).dict()
        )


@app.get("/api/v1/tasks",
    response_model=TaskListResponse,
    summary="List Tasks",
    description="Get a list of all coding tasks with their current status"
)
async def list_tasks(
    page: int = 1,
    page_size: int = 20,
    status_filter: Optional[str] = None,
    engine: WorkflowEngine = Depends(get_workflow_engine)
) -> TaskListResponse:
    """
    📋 **List All Coding Tasks**
    
    Get a paginated list of all coding tasks with filtering options:
    
    - **Pagination**: Control page size and navigate through results
    - **Status Filtering**: Filter by task status (initiated, coding, completed, failed, etc.)
    - **Complete Information**: Full task details including progress and results
    """
    try:
        # Get all tasks
        all_tasks = []
        for task_id in engine.active_workflows.keys():
            task_status = await engine.get_task_status(task_id)
            if task_status:
                # Apply status filter if provided
                if not status_filter or task_status.status.value == status_filter:
                    all_tasks.append(task_status)
        
        # Apply pagination
        total_count = len(all_tasks)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        tasks = all_tasks[start_idx:end_idx]
        
        has_more = end_idx < total_count
        
        return TaskListResponse(
            tasks=tasks,
            total_count=total_count,
            page=page,
            page_size=page_size,
            has_more=has_more
        )
        
    except Exception as e:
        logger.error(f"Failed to list tasks: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                error="ListError",
                message="Failed to retrieve task list",
                details={"error": str(e)},
                timestamp=datetime.utcnow()
            ).dict()
        )


if __name__ == "__main__":
    # Direct execution for development
    settings = get_settings()
    
    uvicorn.run(
        "coding_agent.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.is_development,
        log_level=settings.log_level.lower()
    )