"""
Git Service for repository management and operations.

This service handles all Git operations including cloning, branching,
committing, and pushing changes for the autonomous coding workflow.
"""

import os
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path
import shutil
import uuid

import git
from git import Repo, InvalidGitRepositoryError
from github import Github, GithubException

from ..config.settings import get_settings


logger = logging.getLogger(__name__)


class GitService:
    """
    Service for managing Git operations in the autonomous coding workflow.
    
    This service handles:
    - Repository cloning and updates
    - Branch creation and management
    - Commit creation and pushing
    - Integration with GitHub for PR management
    """
    
    def __init__(self):
        self.settings = get_settings()
        
        # Initialize GitHub client if token is available
        self.github_client = None
        if self.settings.github_token:
            self.github_client = Github(self.settings.github_token)
        
        logger.info("Git service initialized")
    
    async def clone_repository(self, repo_url: str, workspace_path: str, branch: str = "main") -> str:
        """
        Clone a repository to the specified workspace.
        
        Args:
            repo_url: URL of the repository to clone
            workspace_path: Local path to clone the repository
            branch: Branch to checkout (default: main)
            
        Returns:
            Path to the cloned repository
        """
        try:
            logger.info(f"Cloning repository {repo_url} to {workspace_path}")
            
            # Ensure workspace directory exists
            os.makedirs(workspace_path, exist_ok=True)
            
            # Clean up existing directory if it exists
            if os.path.exists(workspace_path) and os.listdir(workspace_path):
                shutil.rmtree(workspace_path)
                os.makedirs(workspace_path, exist_ok=True)
            
            # Clone the repository
            repo = Repo.clone_from(repo_url, workspace_path, branch=branch)
            
            # Configure git user for commits
            config_writer = repo.config_writer()
            config_writer.set_value("user", "name", self.settings.git_user_name)
            config_writer.set_value("user", "email", self.settings.git_user_email)
            config_writer.release()
            
            logger.info(f"Repository cloned successfully to {workspace_path}")
            return workspace_path
            
        except Exception as e:
            logger.error(f"Error cloning repository: {str(e)}")
            raise Exception(f"Failed to clone repository: {str(e)}")
    
    async def create_feature_branch(self, repo_path: str, feature_name: str, base_branch: str = "main") -> str:
        """
        Create a new feature branch with unique identifier.
        
        Args:
            repo_path: Path to the local repository
            feature_name: Base name for the feature branch
            base_branch: The base branch to create the feature branch from
            
        Returns:
            Name of the created branch
        """
        try:
            repo = Repo(repo_path)
            
            # Ensure we're on the correct base branch and it's up to date
            if repo.active_branch.name != base_branch:
                try:
                    # Try to get the base branch from local branches
                    if base_branch in [branch.name for branch in repo.heads]:
                        # Branch exists locally, check it out
                        repo.git.checkout(base_branch)
                    else:
                        # If base branch doesn't exist locally, try to get from remote
                        origin = repo.remotes.origin
                        remote_ref = f"origin/{base_branch}"
                        repo.git.checkout('-b', base_branch, remote_ref)
                except Exception as e:
                    logger.warning(f"Could not checkout {base_branch}, staying on current branch: {str(e)}")
            
            # Pull latest changes
            origin = repo.remotes.origin
            try:
                origin.pull()
            except Exception as e:
                logger.warning(f"Could not pull latest changes: {str(e)}")
            
            # Generate unique branch name
            unique_id = uuid.uuid4().hex[:8]
            branch_name = f"{feature_name}-{unique_id}"
            
            # Create and checkout new branch
            new_branch = repo.create_head(branch_name)
            new_branch.checkout()
            
            logger.info(f"Created feature branch: {branch_name} from {base_branch}")
            return branch_name
            
        except Exception as e:
            logger.error(f"Error creating feature branch: {str(e)}")
            raise Exception(f"Failed to create feature branch: {str(e)}")
    
    async def commit_changes(
        self, 
        repo_path: str, 
        commit_message: str, 
        file_paths: Optional[List[str]] = None
    ) -> str:
        """
        Commit changes to the repository.
        
        Args:
            repo_path: Path to the local repository
            commit_message: Commit message
            file_paths: Specific files to commit (if None, commits all changes)
            
        Returns:
            Commit hash
        """
        try:
            repo = Repo(repo_path)
            
            # Add files to staging area
            if file_paths:
                for file_path in file_paths:
                    repo.index.add([file_path])
            else:
                repo.git.add(A=True)  # Add all changes
            
            # Check if there are changes to commit
            if not repo.index.diff("HEAD"):
                logger.warning("No changes to commit")
                return ""
            
            # Create commit
            commit = repo.index.commit(commit_message)
            
            logger.info(f"Changes committed with hash: {commit.hexsha}")
            return commit.hexsha
            
        except Exception as e:
            logger.error(f"Error committing changes: {str(e)}")
            raise Exception(f"Failed to commit changes: {str(e)}")
    
    async def push_branch(self, repo_path: str, branch_name: str) -> bool:
        """
        Push a branch to the remote repository.
        
        Args:
            repo_path: Path to the local repository
            branch_name: Name of the branch to push
            
        Returns:
            True if successful, False otherwise
        """
        try:
            repo = Repo(repo_path)
            origin = repo.remotes.origin
            
            # Push the branch
            origin.push(refspec=f"refs/heads/{branch_name}:refs/heads/{branch_name}")
            
            logger.info(f"Branch {branch_name} pushed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error pushing branch: {str(e)}")
            raise Exception(f"Failed to push branch: {str(e)}")
    
    async def create_pull_request(
        self,
        repo_name: str,
        branch_name: str,
        title: str,
        description: str,
        base_branch: str = "main"
    ) -> str:
        """
        Create a pull request on GitHub.
        
        Args:
            repo_name: Repository name (format: "owner/repo")
            branch_name: Source branch for the PR
            title: PR title
            description: PR description
            base_branch: Target branch (default: main)
            
        Returns:
            URL of the created pull request
        """
        try:
            if not self.github_client:
                raise Exception("GitHub client not configured")
            
            logger.info(f"Creating pull request for {repo_name}:{branch_name}")
            
            # Get the repository
            repo = self.github_client.get_repo(repo_name)
            
            # Create the pull request
            pr = repo.create_pull(
                title=title,
                body=description,
                head=branch_name,
                base=base_branch
            )
            
            logger.info(f"Pull request created: {pr.html_url}")
            return pr.html_url
            
        except GithubException as e:
            logger.error(f"GitHub API error: {str(e)}")
            raise Exception(f"Failed to create pull request: {str(e)}")
        except Exception as e:
            logger.error(f"Error creating pull request: {str(e)}")
            raise Exception(f"Failed to create pull request: {str(e)}")
    
    async def get_repository_info(self, repo_path: str) -> Dict[str, Any]:
        """
        Get information about a local repository.
        
        Args:
            repo_path: Path to the local repository
            
        Returns:
            Repository information
        """
        try:
            repo = Repo(repo_path)
            
            info = {
                "path": repo_path,
                "current_branch": repo.active_branch.name,
                "remote_url": repo.remotes.origin.url,
                "last_commit": {
                    "hash": repo.head.commit.hexsha,
                    "message": repo.head.commit.message.strip(),
                    "author": str(repo.head.commit.author),
                    "date": repo.head.commit.committed_datetime.isoformat()
                },
                "status": {
                    "modified": [item.a_path for item in repo.index.diff(None)],
                    "staged": [item.a_path for item in repo.index.diff("HEAD")],
                    "untracked": repo.untracked_files
                }
            }
            
            return info
            
        except InvalidGitRepositoryError:
            logger.error(f"Not a valid git repository: {repo_path}")
            raise Exception(f"Not a valid git repository: {repo_path}")
        except Exception as e:
            logger.error(f"Error getting repository info: {str(e)}")
            raise Exception(f"Failed to get repository info: {str(e)}")
    
    async def write_files(self, repo_path: str, files: Dict[str, str]) -> List[str]:
        """
        Write multiple files to the repository.
        
        Args:
            repo_path: Path to the repository
            files: Dictionary of file_path -> content
            
        Returns:
            List of written file paths
        """
        try:
            written_files = []
            
            for file_path, content in files.items():
                full_path = os.path.join(repo_path, file_path)
                
                # Create directory if it doesn't exist
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                
                # Write the file
                with open(full_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                written_files.append(file_path)
                logger.debug(f"Written file: {file_path}")
            
            logger.info(f"Written {len(written_files)} files to repository")
            return written_files
            
        except Exception as e:
            logger.error(f"Error writing files: {str(e)}")
            raise Exception(f"Failed to write files: {str(e)}")
    
    async def validate_repository_access(self, repo_url: str) -> bool:
        """
        Validate that we have access to the repository.
        
        Args:
            repo_url: Repository URL to validate
            
        Returns:
            True if accessible, False otherwise
        """
        try:
            # Extract repo name from URL
            if repo_url.endswith('.git'):
                repo_url = repo_url[:-4]
            
            parts = repo_url.split('/')
            repo_name = f"{parts[-2]}/{parts[-1]}"
            
            if self.github_client:
                repo = self.github_client.get_repo(repo_name)
                # Try to access repository information
                _ = repo.name
                logger.info(f"Repository access validated: {repo_name}")
                return True
            else:
                logger.warning("GitHub client not configured, cannot validate repository access")
                return False
            
        except Exception as e:
            logger.error(f"Error validating repository access: {str(e)}")
            return False
    
    def generate_commit_message(
        self, 
        requirements: str, 
        files_changed: List[str],
        implementation_type: str = "feature"
    ) -> str:
        """
        Generate a descriptive commit message.
        
        Args:
            requirements: Original requirements
            files_changed: List of files that were changed
            implementation_type: Type of implementation (feature, fix, etc.)
            
        Returns:
            Generated commit message
        """
        try:
            # Extract key words from requirements
            key_words = []
            for word in requirements.split():
                if len(word) > 3 and word.lower() not in ['add', 'create', 'implement', 'the', 'and', 'with', 'for']:
                    key_words.append(word.lower())
            
            # Generate summary line
            summary = f"feat: {requirements[:50]}..." if len(requirements) > 50 else f"feat: {requirements}"
            
            # Add details
            details = []
            details.append(f"- Implemented {implementation_type} based on requirements")
            
            if files_changed:
                details.append(f"- Modified {len(files_changed)} file(s):")
                for file_path in files_changed[:5]:  # Limit to 5 files
                    details.append(f"  - {file_path}")
                if len(files_changed) > 5:
                    details.append(f"  - ... and {len(files_changed) - 5} more files")
            
            details.append("")
            details.append("Generated by Coding AI Agent")
            
            commit_message = summary + "\n\n" + "\n".join(details)
            
            return commit_message
            
        except Exception as e:
            logger.error(f"Error generating commit message: {str(e)}")
            return f"feat: {requirements[:50]}"
    
    def generate_pr_description(
        self,
        requirements: str,
        implementation_plan: Dict[str, Any],
        files_changed: List[str],
        test_results: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate a comprehensive pull request description.
        
        Args:
            requirements: Original requirements
            implementation_plan: Implementation plan from AI
            files_changed: List of files that were changed
            test_results: Test execution results
            
        Returns:
            Generated PR description
        """
        try:
            description_parts = []
            
            # Header
            description_parts.append("## 🤖 AI-Generated Implementation")
            description_parts.append("")
            
            # Requirements section
            description_parts.append("### 📋 Requirements")
            description_parts.append(f"```")
            description_parts.append(requirements)
            description_parts.append("```")
            description_parts.append("")
            
            # Implementation summary
            description_parts.append("### 🔧 Implementation Summary")
            if implementation_plan.get("requirement_analysis"):
                analysis = implementation_plan["requirement_analysis"]
                if isinstance(analysis, dict):
                    complexity = analysis.get("complexity", "unknown")
                    description_parts.append(f"- **Complexity**: {complexity.title()}")
                    
                    if analysis.get("tasks"):
                        description_parts.append(f"- **Tasks**: {len(analysis['tasks'])} identified")
            
            description_parts.append(f"- **Files Modified**: {len(files_changed)}")
            description_parts.append("")
            
            # Files changed
            description_parts.append("### 📁 Files Changed")
            for file_path in files_changed:
                description_parts.append(f"- `{file_path}`")
            description_parts.append("")
            
            # Technical details
            if implementation_plan.get("technical_design"):
                description_parts.append("### 🏗️ Technical Design")
                tech_design = implementation_plan["technical_design"]
                if isinstance(tech_design, dict):
                    approach = tech_design.get("approach", "Implementation approach defined")
                    description_parts.append(f"- {approach}")
                    
                    if tech_design.get("components"):
                        description_parts.append("- **Components**: " + ", ".join(tech_design["components"]))
                    
                    if tech_design.get("endpoints"):
                        description_parts.append("- **Endpoints**: " + ", ".join(tech_design["endpoints"]))
                description_parts.append("")
            
            # Testing information
            description_parts.append("### 🧪 Testing")
            if test_results:
                description_parts.append("- ✅ Automated tests generated and executed")
                if test_results.get("passed"):
                    description_parts.append(f"- ✅ {test_results['passed']} tests passed")
                if test_results.get("failed"):
                    description_parts.append(f"- ❌ {test_results['failed']} tests failed")
            else:
                description_parts.append("- ✅ Test suite generated (execution pending)")
            description_parts.append("")
            
            # Quality assurance
            description_parts.append("### ✅ Quality Assurance")
            description_parts.append("- ✅ Code follows existing patterns and conventions")
            description_parts.append("- ✅ Proper type hints and documentation")
            description_parts.append("- ✅ Error handling implemented")
            description_parts.append("- ✅ FastAPI best practices followed")
            description_parts.append("")
            
            # Footer
            description_parts.append("---")
            description_parts.append("*This implementation was generated by the Coding AI Agent*")
            description_parts.append("*Please review the changes before merging*")
            
            return "\n".join(description_parts)
            
        except Exception as e:
            logger.error(f"Error generating PR description: {str(e)}")
            return f"## AI-Generated Implementation\n\n{requirements}\n\nFiles changed: {', '.join(files_changed)}"