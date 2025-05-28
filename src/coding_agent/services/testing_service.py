"""
Testing Service - Manages isolated testing environments and test execution.

This service provides comprehensive testing capabilities including:
- Docker-based isolated testing environments
- Dependency installation and management
- Service startup and health validation
- Test execution and result tracking
- Resource cleanup and management
"""

import asyncio
import logging
import os
import tempfile
import shutil
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Union
from pathlib import Path
import subprocess
import json
import uuid

from ..models.testing import (
    TestEnvironment, TestResults, TestDetail, 
    EnvironmentStatus, TestType, TestSuite
)
from ..config.settings import get_settings
from .docker_service import DockerEnvironmentService


logger = logging.getLogger(__name__)


class TestingService:
    """
    Comprehensive testing service for isolated code validation.
    
    This service manages the complete testing lifecycle:
    1. Environment creation and setup
    2. Dependency installation and configuration
    3. Service startup and health validation
    4. Test execution and result collection
    5. Resource cleanup and management
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.docker_service = DockerEnvironmentService()
        self.active_environments: Dict[str, TestEnvironment] = {}
        
        # Ensure testing directory exists
        self.testing_base_path = os.path.join(self.settings.workspace_base_path, "testing")
        os.makedirs(self.testing_base_path, exist_ok=True)
        
        logger.info("Testing service initialized")
    
    async def create_test_environment(
        self, 
        task_id: str, 
        target_service: str = "market-predictor",
        python_version: str = "3.9"
    ) -> TestEnvironment:
        """
        Create an isolated testing environment.
        
        Args:
            task_id: Unique task identifier
            target_service: Target service name
            python_version: Python version for the environment
            
        Returns:
            Created test environment
        """
        try:
            logger.info(f"Creating test environment for task {task_id}")
            
            # Generate unique environment ID
            env_id = f"test-env-{task_id}-{uuid.uuid4().hex[:8]}"
            
            # Create environment workspace
            env_workspace = os.path.join(self.testing_base_path, env_id)
            os.makedirs(env_workspace, exist_ok=True)
            
            # Create Docker container for isolated testing
            container = await self.docker_service.create_container(
                env_id=env_id,
                image=f"python:{python_version}-slim",
                workspace_path=env_workspace
            )
            
            # Create test environment object
            environment = TestEnvironment(
                env_id=env_id,
                task_id=task_id,
                container_id=container.id if container else None,
                status=EnvironmentStatus.CREATING,
                target_service=target_service,
                python_version=python_version,
                workspace_path=env_workspace,
                created_at=datetime.utcnow()
            )
            
            # Store in active environments
            self.active_environments[env_id] = environment
            
            # If container creation succeeded, mark as ready
            if container:
                environment.status = EnvironmentStatus.READY
                environment.container_info = {
                    "id": container.id,
                    "name": container.name,
                    "status": container.status
                }
                logger.info(f"Test environment {env_id} created successfully")
            else:
                environment.status = EnvironmentStatus.FAILED
                environment.error_message = "Failed to create Docker container"
                logger.error(f"Failed to create container for environment {env_id}")
            
            return environment
            
        except Exception as e:
            logger.error(f"Error creating test environment: {str(e)}")
            # Create a failed environment record
            environment = TestEnvironment(
                env_id=f"failed-{task_id}",
                task_id=task_id,
                status=EnvironmentStatus.FAILED,
                target_service=target_service,
                python_version=python_version,
                error_message=str(e),
                created_at=datetime.utcnow()
            )
            return environment
    
    async def install_dependencies(
        self, 
        environment: TestEnvironment, 
        requirements_file: Optional[str] = None,
        additional_packages: Optional[List[str]] = None
    ) -> bool:
        """
        Install dependencies in the test environment.
        
        Args:
            environment: Test environment
            requirements_file: Path to requirements.txt file
            additional_packages: Additional packages to install
            
        Returns:
            True if installation successful, False otherwise
        """
        try:
            logger.info(f"Installing dependencies in environment {environment.env_id}")
            
            if environment.status != EnvironmentStatus.READY:
                raise ValueError(f"Environment {environment.env_id} is not ready")
            
            environment.status = EnvironmentStatus.INSTALLING_DEPS
            
            # Prepare installation commands
            install_commands = []
            
            # Update pip first
            install_commands.append("pip install --upgrade pip")
            
            # Install from requirements file if provided
            if requirements_file and os.path.exists(requirements_file):
                container_req_path = "/app/requirements.txt"
                # Copy requirements file to container
                await self.docker_service.copy_file_to_container(
                    environment.container_id,
                    requirements_file,
                    container_req_path
                )
                install_commands.append(f"pip install -r {container_req_path}")
            
            # Install additional packages
            if additional_packages:
                for package in additional_packages:
                    install_commands.append(f"pip install {package}")
            
            # Install testing dependencies
            test_packages = [
                "pytest>=7.4.0",
                "pytest-asyncio>=0.21.0", 
                "pytest-cov>=4.1.0",
                "httpx>=0.25.0",
                "requests>=2.31.0"
            ]
            
            for package in test_packages:
                install_commands.append(f"pip install {package}")
            
            # Execute installation commands
            for command in install_commands:
                result = await self.docker_service.execute_command(
                    environment.container_id,
                    command,
                    timeout=300  # 5 minutes timeout
                )
                
                if result.exit_code != 0:
                    error_msg = f"Failed to execute: {command}. Error: {result.stderr}"
                    environment.error_message = error_msg
                    environment.status = EnvironmentStatus.FAILED
                    logger.error(error_msg)
                    return False
            
            environment.status = EnvironmentStatus.READY
            environment.dependencies_installed = True
            logger.info(f"Dependencies installed successfully in {environment.env_id}")
            return True
            
        except Exception as e:
            error_msg = f"Error installing dependencies: {str(e)}"
            environment.error_message = error_msg
            environment.status = EnvironmentStatus.FAILED
            logger.error(error_msg)
            return False
    
    async def start_target_service(
        self, 
        environment: TestEnvironment,
        service_path: str,
        port: int = 8000
    ) -> bool:
        """
        Start the target service in the test environment.
        
        Args:
            environment: Test environment
            service_path: Path to the service code
            port: Port to run the service on
            
        Returns:
            True if service started successfully, False otherwise
        """
        try:
            logger.info(f"Starting {environment.target_service} in environment {environment.env_id}")
            
            if environment.status != EnvironmentStatus.READY:
                raise ValueError(f"Environment {environment.env_id} is not ready")
            
            environment.status = EnvironmentStatus.STARTING_SERVICE
            
            # Copy service code to container
            container_service_path = f"/app/{environment.target_service}"
            await self.docker_service.copy_directory_to_container(
                environment.container_id,
                service_path,
                container_service_path
            )
            
            # Start the service in background
            start_command = f"cd {container_service_path} && python -m uvicorn main:app --host 0.0.0.0 --port {port}"
            
            # Execute service start command in background
            result = await self.docker_service.execute_command_background(
                environment.container_id,
                start_command
            )
            
            if result.success:
                # Wait for service to start and check health
                await asyncio.sleep(3)  # Give service time to start
                
                health_result = await self.docker_service.execute_command(
                    environment.container_id,
                    f"curl -s http://localhost:{port}/health || echo 'HEALTH_CHECK_FAILED'"
                )
                
                if "HEALTH_CHECK_FAILED" not in health_result.stdout:
                    environment.status = EnvironmentStatus.SERVICE_RUNNING
                    environment.service_port = port
                    environment.service_started = True
                    logger.info(f"Service started successfully in {environment.env_id}")
                    return True
                else:
                    environment.error_message = "Service health check failed"
                    environment.status = EnvironmentStatus.FAILED
                    return False
            else:
                environment.error_message = f"Failed to start service: {result.error}"
                environment.status = EnvironmentStatus.FAILED
                return False
                
        except Exception as e:
            error_msg = f"Error starting service: {str(e)}"
            environment.error_message = error_msg
            environment.status = EnvironmentStatus.FAILED
            logger.error(error_msg)
            return False
    
    async def run_test_suite(
        self, 
        environment: TestEnvironment,
        test_suite: TestSuite
    ) -> TestResults:
        """
        Run a complete test suite in the environment.
        
        Args:
            environment: Test environment
            test_suite: Test suite configuration
            
        Returns:
            Test execution results
        """
        try:
            logger.info(f"Running test suite in environment {environment.env_id}")
            
            if environment.status not in [EnvironmentStatus.READY, EnvironmentStatus.SERVICE_RUNNING]:
                raise ValueError(f"Environment {environment.env_id} is not ready for testing")
            
            environment.status = EnvironmentStatus.RUNNING_TESTS
            
            # Copy test files to container
            for test_file_path, test_content in test_suite.test_files.items():
                container_test_path = f"/app/tests/{os.path.basename(test_file_path)}"
                await self.docker_service.write_file_in_container(
                    environment.container_id,
                    container_test_path,
                    test_content
                )
            
            # Copy source files if provided
            if test_suite.source_files:
                for source_file_path, source_content in test_suite.source_files.items():
                    container_source_path = f"/app/{os.path.basename(source_file_path)}"
                    await self.docker_service.write_file_in_container(
                        environment.container_id,
                        container_source_path,
                        source_content
                    )
            
            # Execute test suite
            test_results = TestResults(
                test_type=test_suite.test_type,
                environment_id=environment.env_id,
                started_at=datetime.utcnow()
            )
            
            # Run different types of tests based on test suite type
            if test_suite.test_type == TestType.UNIT:
                await self._run_unit_tests(environment, test_results)
            elif test_suite.test_type == TestType.INTEGRATION:
                await self._run_integration_tests(environment, test_results)
            elif test_suite.test_type == TestType.API:
                await self._run_api_tests(environment, test_results)
            else:
                # Run all tests
                await self._run_all_tests(environment, test_results)
            
            test_results.completed_at = datetime.utcnow()
            if test_results.started_at:
                test_results.execution_time = (test_results.completed_at - test_results.started_at).total_seconds()
            
            environment.status = EnvironmentStatus.READY
            logger.info(f"Test suite completed in {environment.env_id}")
            
            return test_results
            
        except Exception as e:
            error_msg = f"Error running test suite: {str(e)}"
            environment.error_message = error_msg
            environment.status = EnvironmentStatus.FAILED
            logger.error(error_msg)
            
            return TestResults(
                test_type=test_suite.test_type,
                environment_id=environment.env_id,
                passed=0,
                failed=1,
                total=1,
                success=False,
                error_message=error_msg,
                started_at=datetime.utcnow(),
                completed_at=datetime.utcnow()
            )
    
    async def _run_unit_tests(self, environment: TestEnvironment, results: TestResults):
        """Run unit tests in the environment."""
        # Execute pytest for unit tests - use /bin/bash -c to ensure proper command execution
        command = "/bin/bash -c 'cd /app && python -m pytest tests/ -v --tb=short --json-report --json-report-file=/tmp/test_results.json'"
        
        exec_result = await self.docker_service.execute_command(
            environment.container_id,
            command,
            timeout=300
        )
        
        await self._parse_test_results(environment, exec_result, results)
    
    async def _run_integration_tests(self, environment: TestEnvironment, results: TestResults):
        """Run integration tests in the environment."""
        # Execute pytest for integration tests
        command = "/bin/bash -c 'cd /app && python -m pytest tests/ -k integration -v --tb=short --json-report --json-report-file=/tmp/test_results.json'"
        
        exec_result = await self.docker_service.execute_command(
            environment.container_id,
            command,
            timeout=600
        )
        
        await self._parse_test_results(environment, exec_result, results)
    
    async def _run_api_tests(self, environment: TestEnvironment, results: TestResults):
        """Run API tests in the environment."""
        # Execute pytest for API tests
        command = "/bin/bash -c 'cd /app && python -m pytest tests/ -k api -v --tb=short --json-report --json-report-file=/tmp/test_results.json'"
        
        exec_result = await self.docker_service.execute_command(
            environment.container_id,
            command,
            timeout=600
        )
        
        await self._parse_test_results(environment, exec_result, results)
    
    async def _run_all_tests(self, environment: TestEnvironment, results: TestResults):
        """Run all tests in the environment."""
        # Execute complete test suite
        command = "/bin/bash -c 'cd /app && python -m pytest tests/ -v --tb=short --cov=. --cov-report=json --json-report --json-report-file=/tmp/test_results.json'"
        
        exec_result = await self.docker_service.execute_command(
            environment.container_id,
            command,
            timeout=900
        )
        
        await self._parse_test_results(environment, exec_result, results)
    
    async def _parse_test_results(self, environment: TestEnvironment, exec_result, results: TestResults):
        """Parse test execution results."""
        try:
            # Try to get JSON results file
            json_result = await self.docker_service.execute_command(
                environment.container_id,
                "cat /tmp/test_results.json",
                timeout=30
            )
            
            if json_result.exit_code == 0:
                test_data = json.loads(json_result.stdout)
                
                results.passed = test_data.get("summary", {}).get("passed", 0)
                results.failed = test_data.get("summary", {}).get("failed", 0)
                results.skipped = test_data.get("summary", {}).get("skipped", 0)
                results.total = results.passed + results.failed + results.skipped
                
                # Parse individual test details
                for test in test_data.get("tests", []):
                    detail = TestDetail(
                        test_name=test.get("nodeid", "unknown"),
                        status="passed" if test.get("outcome") == "passed" else "failed",
                        duration_seconds=test.get("duration", 0),
                        error_message=test.get("longrepr") if test.get("outcome") != "passed" else None
                    )
                    results.test_details.append(detail)
                
                results.success = results.failed == 0
            else:
                # Fallback to parsing stdout/stderr
                output = exec_result.stdout + exec_result.stderr
                results.total = 1
                if exec_result.exit_code == 0:
                    results.passed = 1
                    results.success = True
                else:
                    results.failed = 1
                    results.success = False
                    results.error_message = output
                    
        except Exception as e:
            logger.error(f"Error parsing test results: {str(e)}")
            results.total = 1
            results.failed = 1
            results.success = False
            results.error_message = f"Failed to parse test results: {str(e)}"
    
    async def cleanup_environment(self, environment: TestEnvironment) -> bool:
        """
        Clean up test environment and resources.
        
        Args:
            environment: Test environment to cleanup
            
        Returns:
            True if cleanup successful, False otherwise
        """
        try:
            logger.info(f"Cleaning up environment {environment.env_id}")
            
            # Stop and remove Docker container
            if environment.container_id:
                await self.docker_service.cleanup_container(environment.container_id)
            
            # Remove workspace directory
            if environment.workspace_path and os.path.exists(environment.workspace_path):
                shutil.rmtree(environment.workspace_path, ignore_errors=True)
            
            # Remove from active environments
            if environment.env_id in self.active_environments:
                del self.active_environments[environment.env_id]
            
            environment.status = EnvironmentStatus.CLEANED_UP
            logger.info(f"Environment {environment.env_id} cleaned up successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error cleaning up environment {environment.env_id}: {str(e)}")
            return False
    
    def get_environment_status(self, env_id: str) -> Optional[TestEnvironment]:
        """Get the status of a test environment."""
        return self.active_environments.get(env_id)
    
    def list_active_environments(self) -> List[TestEnvironment]:
        """List all active test environments."""
        return list(self.active_environments.values())
    
    async def cleanup_expired_environments(self, max_age_hours: int = 24):
        """Clean up environments older than specified age."""
        try:
            current_time = datetime.utcnow()
            expired_envs = []
            
            for env in self.active_environments.values():
                if env.created_at:
                    age = current_time - env.created_at
                    if age > timedelta(hours=max_age_hours):
                        expired_envs.append(env)
            
            for env in expired_envs:
                await self.cleanup_environment(env)
                
            if expired_envs:
                logger.info(f"Cleaned up {len(expired_envs)} expired environments")
                
        except Exception as e:
            logger.error(f"Error cleaning up expired environments: {str(e)}") 