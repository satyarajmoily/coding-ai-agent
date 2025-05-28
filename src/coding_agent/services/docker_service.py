"""
Docker Environment Service - Manages Docker containers for isolated testing.

This service handles Docker container lifecycle management for testing:
- Container creation and configuration
- File operations within containers
- Command execution and result handling
- Container cleanup and resource management
"""

import asyncio
import logging
import os
import tempfile
import tarfile
import io
from typing import Dict, Any, Optional, List
from datetime import datetime
import docker
from docker.models.containers import Container
from docker.errors import DockerException, APIError

from ..models.testing import CommandResult, ContainerInfo
from ..config.settings import get_settings


logger = logging.getLogger(__name__)


class DockerEnvironmentService:
    """
    Service for managing Docker containers for isolated testing environments.
    
    This service provides comprehensive container management capabilities:
    - Container lifecycle management
    - File and directory operations
    - Command execution with proper error handling
    - Resource monitoring and cleanup
    """
    
    def __init__(self):
        self.settings = get_settings()
        
        try:
            # Initialize Docker client
            self.docker_client = docker.from_env()
            
            # Test Docker connectivity
            self.docker_client.ping()
            logger.info("Docker service initialized successfully")
            
        except DockerException as e:
            logger.error(f"Failed to initialize Docker client: {str(e)}")
            self.docker_client = None
        
        # Track active containers
        self.active_containers: Dict[str, ContainerInfo] = {}
    
    async def create_container(
        self, 
        env_id: str,
        image: str = "python:3.9-slim",
        workspace_path: str = None
    ) -> Optional[Container]:
        """
        Create a new Docker container for testing.
        
        Args:
            env_id: Environment identifier
            image: Docker image to use
            workspace_path: Host workspace path to mount
            
        Returns:
            Created container object or None if failed
        """
        try:
            if not self.docker_client:
                raise Exception("Docker client not available")
            
            logger.info(f"Creating Docker container for environment {env_id}")
            
            # Container configuration
            container_name = f"coding-agent-test-{env_id}"
            
            # Prepare environment variables
            env_vars = {
                "PYTHONPATH": "/app",
                "PYTHONUNBUFFERED": "1",
                "ENV_ID": env_id
            }
            
            # Prepare volumes if workspace provided
            volumes = {}
            if workspace_path and os.path.exists(workspace_path):
                volumes[workspace_path] = {"bind": "/workspace", "mode": "rw"}
            
            # Create container
            container = self.docker_client.containers.run(
                image=image,
                name=container_name,
                command="tail -f /dev/null",  # Keep container running
                detach=True,
                environment=env_vars,
                volumes=volumes,
                working_dir="/app",
                network_mode=self.settings.docker_network_mode,
                mem_limit="1g",  # Memory limit
                cpu_count=1,     # CPU limit
                remove=False,    # Don't auto-remove for debugging
                tty=True,
                stdin_open=True
            )
            
            # Create container info object
            container_info = ContainerInfo(
                container_id=container.id,
                env_id=env_id,
                name=container_name,
                image=image,
                status="running",
                created_at=datetime.utcnow(),
                workspace_path=workspace_path
            )
            
            # Store in active containers
            self.active_containers[container.id] = container_info
            
            # Set up basic directory structure in container
            await self._setup_container_structure(container)
            
            logger.info(f"Container {container_name} created successfully")
            return container
            
        except Exception as e:
            logger.error(f"Failed to create container for {env_id}: {str(e)}")
            return None
    
    async def _setup_container_structure(self, container: Container):
        """Set up basic directory structure in the container."""
        try:
            # Create necessary directories
            directories = ["/app", "/app/tests", "/app/src", "/tmp"]
            
            for directory in directories:
                result = container.exec_run(f"mkdir -p {directory}")
                if result.exit_code != 0:
                    logger.warning(f"Failed to create directory {directory}: {result.output.decode()}")
            
            # Install basic system dependencies
            system_packages = [
                "apt-get update",
                "apt-get install -y curl wget git build-essential",
                "apt-get clean"
            ]
            
            for cmd in system_packages:
                result = container.exec_run(f"sh -c '{cmd}'")
                if result.exit_code != 0:
                    logger.warning(f"Failed to execute: {cmd}")
            
        except Exception as e:
            logger.error(f"Error setting up container structure: {str(e)}")
    
    async def execute_command(
        self, 
        container_id: str, 
        command: str,
        timeout: int = 60,
        working_dir: str = "/app"
    ) -> CommandResult:
        """
        Execute a command in the container.
        
        Args:
            container_id: Container ID
            command: Command to execute
            timeout: Command timeout in seconds
            working_dir: Working directory for command execution
            
        Returns:
            Command execution result
        """
        try:
            if not self.docker_client:
                raise Exception("Docker client not available")
            
            container = self.docker_client.containers.get(container_id)
            
            logger.debug(f"Executing command in {container_id}: {command}")
            
            # Execute command with timeout
            result = await asyncio.wait_for(
                asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: container.exec_run(
                        command,
                        workdir=working_dir,
                        environment={"PYTHONPATH": "/app"}
                    )
                ),
                timeout=timeout
            )
            
            # Decode output
            stdout = result.output.decode('utf-8') if result.output else ""
            stderr = ""  # Docker exec_run combines stdout and stderr
            
            return CommandResult(
                exit_code=result.exit_code,
                stdout=stdout,
                stderr=stderr,
                command=command,
                duration_seconds=0  # TODO: Add timing
            )
            
        except asyncio.TimeoutError:
            logger.error(f"Command timeout after {timeout}s: {command}")
            return CommandResult(
                exit_code=124,  # Timeout exit code
                stdout="",
                stderr=f"Command timed out after {timeout} seconds",
                command=command,
                duration_seconds=timeout
            )
        except Exception as e:
            logger.error(f"Error executing command: {str(e)}")
            return CommandResult(
                exit_code=1,
                stdout="",
                stderr=str(e),
                command=command,
                duration_seconds=0
            )
    
    async def execute_command_background(
        self, 
        container_id: str, 
        command: str
    ) -> CommandResult:
        """
        Execute a command in the background (non-blocking).
        
        Args:
            container_id: Container ID
            command: Command to execute in background
            
        Returns:
            Command execution result (immediate)
        """
        try:
            if not self.docker_client:
                raise Exception("Docker client not available")
            
            container = self.docker_client.containers.get(container_id)
            
            logger.debug(f"Executing background command in {container_id}: {command}")
            
            # Execute in background using nohup
            bg_command = f"nohup {command} > /tmp/bg_output.log 2>&1 &"
            
            result = container.exec_run(bg_command, detach=True)
            
            return CommandResult(
                exit_code=0,  # Background command started
                stdout="Background command started",
                stderr="",
                command=command,
                duration_seconds=0,
                success=True
            )
            
        except Exception as e:
            logger.error(f"Error executing background command: {str(e)}")
            return CommandResult(
                exit_code=1,
                stdout="",
                stderr=str(e),
                command=command,
                duration_seconds=0,
                success=False,
                error=str(e)
            )
    
    async def copy_file_to_container(
        self, 
        container_id: str, 
        host_path: str, 
        container_path: str
    ) -> bool:
        """
        Copy a file from host to container.
        
        Args:
            container_id: Container ID
            host_path: Source file path on host
            container_path: Destination path in container
            
        Returns:
            True if copy successful, False otherwise
        """
        try:
            if not self.docker_client:
                raise Exception("Docker client not available")
            
            container = self.docker_client.containers.get(container_id)
            
            if not os.path.exists(host_path):
                raise FileNotFoundError(f"Host file not found: {host_path}")
            
            # Create a tar archive with the file
            tar_buffer = io.BytesIO()
            with tarfile.open(fileobj=tar_buffer, mode='w') as tar:
                tar.add(host_path, arcname=os.path.basename(container_path))
            tar_buffer.seek(0)
            
            # Copy to container
            container.put_archive(
                path=os.path.dirname(container_path),
                data=tar_buffer.getvalue()
            )
            
            logger.debug(f"File copied: {host_path} -> {container_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error copying file to container: {str(e)}")
            return False
    
    async def copy_directory_to_container(
        self, 
        container_id: str, 
        host_dir: str, 
        container_dir: str
    ) -> bool:
        """
        Copy a directory from host to container.
        
        Args:
            container_id: Container ID
            host_dir: Source directory path on host
            container_dir: Destination directory in container
            
        Returns:
            True if copy successful, False otherwise
        """
        try:
            if not self.docker_client:
                raise Exception("Docker client not available")
            
            container = self.docker_client.containers.get(container_id)
            
            if not os.path.exists(host_dir):
                raise FileNotFoundError(f"Host directory not found: {host_dir}")
            
            # Create tar archive of the directory
            tar_buffer = io.BytesIO()
            with tarfile.open(fileobj=tar_buffer, mode='w') as tar:
                tar.add(host_dir, arcname=os.path.basename(container_dir))
            tar_buffer.seek(0)
            
            # Copy to container
            container.put_archive(
                path=os.path.dirname(container_dir),
                data=tar_buffer.getvalue()
            )
            
            logger.debug(f"Directory copied: {host_dir} -> {container_dir}")
            return True
            
        except Exception as e:
            logger.error(f"Error copying directory to container: {str(e)}")
            return False
    
    async def write_file_in_container(
        self, 
        container_id: str, 
        file_path: str, 
        content: str
    ) -> bool:
        """
        Write content to a file in the container.
        
        Args:
            container_id: Container ID
            file_path: File path in container
            content: Content to write
            
        Returns:
            True if write successful, False otherwise
        """
        try:
            if not self.docker_client:
                raise Exception("Docker client not available")
            
            container = self.docker_client.containers.get(container_id)
            
            # Create directory if it doesn't exist
            dir_path = os.path.dirname(file_path)
            if dir_path:
                result = container.exec_run(f"mkdir -p {dir_path}")
                if result.exit_code != 0:
                    logger.warning(f"Failed to create directory {dir_path}")
            
            # Create temporary file on host
            with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp_file:
                temp_file.write(content)
                temp_file_path = temp_file.name
            
            try:
                # Copy file to container
                success = await self.copy_file_to_container(
                    container_id, temp_file_path, file_path
                )
                return success
            finally:
                # Clean up temporary file
                os.unlink(temp_file_path)
                
        except Exception as e:
            logger.error(f"Error writing file in container: {str(e)}")
            return False
    
    async def get_container_logs(self, container_id: str, tail: int = 100) -> str:
        """
        Get logs from a container.
        
        Args:
            container_id: Container ID
            tail: Number of lines to tail
            
        Returns:
            Container logs as string
        """
        try:
            if not self.docker_client:
                raise Exception("Docker client not available")
            
            container = self.docker_client.containers.get(container_id)
            logs = container.logs(tail=tail).decode('utf-8')
            return logs
            
        except Exception as e:
            logger.error(f"Error getting container logs: {str(e)}")
            return f"Error retrieving logs: {str(e)}"
    
    async def cleanup_container(self, container_id: str) -> bool:
        """
        Stop and remove a container.
        
        Args:
            container_id: Container ID to cleanup
            
        Returns:
            True if cleanup successful, False otherwise
        """
        try:
            if not self.docker_client:
                raise Exception("Docker client not available")
            
            container = self.docker_client.containers.get(container_id)
            
            # Stop container
            container.stop(timeout=10)
            
            # Remove container
            container.remove(force=True)
            
            # Remove from active containers
            if container_id in self.active_containers:
                del self.active_containers[container_id]
            
            logger.info(f"Container {container_id} cleaned up successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error cleaning up container {container_id}: {str(e)}")
            return False
    
    def get_container_info(self, container_id: str) -> Optional[ContainerInfo]:
        """Get information about a container."""
        return self.active_containers.get(container_id)
    
    def list_active_containers(self) -> List[ContainerInfo]:
        """List all active containers."""
        return list(self.active_containers.values())
    
    async def cleanup_all_containers(self):
        """Clean up all active containers."""
        try:
            container_ids = list(self.active_containers.keys())
            
            for container_id in container_ids:
                await self.cleanup_container(container_id)
            
            logger.info(f"Cleaned up {len(container_ids)} containers")
            
        except Exception as e:
            logger.error(f"Error cleaning up all containers: {str(e)}")
    
    def is_docker_available(self) -> bool:
        """Check if Docker is available and accessible."""
        try:
            if self.docker_client:
                self.docker_client.ping()
                return True
            return False
        except Exception:
            return False 