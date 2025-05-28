"""
Code Analysis Service for understanding existing codebases.

This service analyzes target repositories to understand patterns,
conventions, and structures that guide code generation.
"""

import os
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path
import ast
import json

from ..config.settings import get_settings


logger = logging.getLogger(__name__)


class CodeAnalysisService:
    """
    Service for analyzing existing codebases to understand patterns and conventions.
    
    This service examines target repositories to extract:
    - Project structure and organization
    - Coding patterns and conventions
    - API design patterns
    - Dependencies and integrations
    """
    
    def __init__(self):
        self.settings = get_settings()
    
    async def analyze_repository(self, repo_path: str) -> Dict[str, Any]:
        """
        Analyze a repository to extract patterns and conventions.
        
        Args:
            repo_path: Path to the repository to analyze
            
        Returns:
            Analysis results with patterns and structure information
        """
        try:
            logger.info(f"Analyzing repository: {repo_path}")
            
            if not os.path.exists(repo_path):
                raise ValueError(f"Repository path does not exist: {repo_path}")
            
            analysis = {
                "repository_path": repo_path,
                "structure": await self._analyze_structure(repo_path),
                "patterns": await self._analyze_code_patterns(repo_path),
                "dependencies": await self._analyze_dependencies(repo_path),
                "api_patterns": await self._analyze_api_patterns(repo_path),
                "test_patterns": await self._analyze_test_patterns(repo_path),
                "configuration": await self._analyze_configuration(repo_path)
            }
            
            logger.info("Repository analysis completed successfully")
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing repository: {str(e)}")
            raise Exception(f"Failed to analyze repository: {str(e)}")
    
    async def _analyze_structure(self, repo_path: str) -> Dict[str, Any]:
        """Analyze the project structure and organization."""
        try:
            structure = {
                "directories": [],
                "python_files": [],
                "test_files": [],
                "config_files": [],
                "main_modules": []
            }
            
            for root, dirs, files in os.walk(repo_path):
                # Skip common ignored directories
                dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['__pycache__', 'venv', 'node_modules']]
                
                rel_root = os.path.relpath(root, repo_path)
                if rel_root != '.':
                    structure["directories"].append(rel_root)
                
                for file in files:
                    file_path = os.path.join(rel_root, file) if rel_root != '.' else file
                    
                    if file.endswith('.py'):
                        structure["python_files"].append(file_path)
                        if file.startswith('test_') or 'test' in file_path:
                            structure["test_files"].append(file_path)
                        elif file in ['main.py', 'app.py', '__init__.py']:
                            structure["main_modules"].append(file_path)
                    
                    elif file in ['requirements.txt', 'pyproject.toml', 'setup.py', '.env', 'docker-compose.yml']:
                        structure["config_files"].append(file_path)
            
            return structure
            
        except Exception as e:
            logger.error(f"Error analyzing structure: {str(e)}")
            return {}
    
    async def _analyze_code_patterns(self, repo_path: str) -> Dict[str, Any]:
        """Analyze coding patterns and conventions."""
        try:
            patterns = {
                "naming_conventions": {
                    "functions": [],
                    "classes": [],
                    "variables": []
                },
                "import_patterns": [],
                "docstring_style": "unknown",
                "type_hints_usage": False,
                "async_patterns": False,
                "error_handling": []
            }
            
            # Analyze Python files
            for root, dirs, files in os.walk(repo_path):
                dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['__pycache__', 'venv']]
                
                for file in files:
                    if file.endswith('.py') and not file.startswith('test_'):
                        file_path = os.path.join(root, file)
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                content = f.read()
                                tree = ast.parse(content)
                                self._extract_patterns_from_ast(tree, patterns)
                        except Exception as e:
                            logger.debug(f"Could not parse {file_path}: {str(e)}")
                            continue
            
            # Deduplicate and summarize patterns
            patterns["naming_conventions"]["functions"] = list(set(patterns["naming_conventions"]["functions"]))[:10]
            patterns["naming_conventions"]["classes"] = list(set(patterns["naming_conventions"]["classes"]))[:10]
            patterns["import_patterns"] = list(set(patterns["import_patterns"]))[:20]
            
            return patterns
            
        except Exception as e:
            logger.error(f"Error analyzing code patterns: {str(e)}")
            return {}
    
    def _extract_patterns_from_ast(self, tree: ast.AST, patterns: Dict[str, Any]):
        """Extract patterns from an AST."""
        for node in ast.walk(tree):
            # Function names
            if isinstance(node, ast.FunctionDef):
                patterns["naming_conventions"]["functions"].append(node.name)
                
                # Check for async patterns
                if isinstance(node, ast.AsyncFunctionDef):
                    patterns["async_patterns"] = True
                
                # Check for type hints
                if node.returns or any(arg.annotation for arg in node.args.args):
                    patterns["type_hints_usage"] = True
                
                # Check for docstrings
                if (node.body and isinstance(node.body[0], ast.Expr) and 
                    isinstance(node.body[0].value, ast.Str)):
                    if '"""' in node.body[0].value.s:
                        patterns["docstring_style"] = "triple_quotes"
            
            # Class names
            elif isinstance(node, ast.ClassDef):
                patterns["naming_conventions"]["classes"].append(node.name)
            
            # Import patterns
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    patterns["import_patterns"].append(f"import {alias.name}")
            
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    patterns["import_patterns"].append(f"from {node.module}")
            
            # Error handling patterns
            elif isinstance(node, ast.Try):
                patterns["error_handling"].append("try_except_block")
            elif isinstance(node, ast.Raise):
                patterns["error_handling"].append("raise_exception")
    
    async def _analyze_dependencies(self, repo_path: str) -> Dict[str, Any]:
        """Analyze project dependencies."""
        try:
            dependencies = {
                "requirements": [],
                "dev_requirements": [],
                "fastapi_version": None,
                "python_version": None
            }
            
            # Check requirements.txt
            req_file = os.path.join(repo_path, "requirements.txt")
            if os.path.exists(req_file):
                with open(req_file, 'r') as f:
                    dependencies["requirements"] = [line.strip() for line in f if line.strip() and not line.startswith('#')]
            
            # Check requirements-dev.txt
            dev_req_file = os.path.join(repo_path, "requirements-dev.txt")
            if os.path.exists(dev_req_file):
                with open(dev_req_file, 'r') as f:
                    dependencies["dev_requirements"] = [line.strip() for line in f if line.strip() and not line.startswith('#')]
            
            # Extract specific versions
            for req in dependencies["requirements"]:
                if req.startswith("fastapi"):
                    dependencies["fastapi_version"] = req
                elif req.startswith("python"):
                    dependencies["python_version"] = req
            
            return dependencies
            
        except Exception as e:
            logger.error(f"Error analyzing dependencies: {str(e)}")
            return {}
    
    async def _analyze_api_patterns(self, repo_path: str) -> Dict[str, Any]:
        """Analyze FastAPI patterns and conventions."""
        try:
            api_patterns = {
                "endpoint_patterns": [],
                "response_models": [],
                "request_models": [],
                "status_codes": [],
                "middleware_usage": False,
                "dependency_injection": False
            }
            
            # Look for FastAPI files
            for root, dirs, files in os.walk(repo_path):
                dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['__pycache__', 'venv']]
                
                for file in files:
                    if file.endswith('.py'):
                        file_path = os.path.join(root, file)
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                content = f.read()
                                
                                # Check for FastAPI patterns
                                if 'from fastapi' in content or 'import fastapi' in content:
                                    api_patterns.update(self._extract_fastapi_patterns(content))
                        
                        except Exception as e:
                            logger.debug(f"Could not analyze {file_path}: {str(e)}")
                            continue
            
            return api_patterns
            
        except Exception as e:
            logger.error(f"Error analyzing API patterns: {str(e)}")
            return {}
    
    def _extract_fastapi_patterns(self, content: str) -> Dict[str, Any]:
        """Extract FastAPI-specific patterns from code content."""
        patterns = {
            "endpoint_patterns": [],
            "response_models": [],
            "status_codes": []
        }
        
        lines = content.split('\n')
        
        for line in lines:
            stripped = line.strip()
            
            # API endpoint patterns
            if stripped.startswith('@app.') or stripped.startswith('@router.'):
                patterns["endpoint_patterns"].append(stripped)
            
            # Response models
            if 'response_model=' in stripped:
                patterns["response_models"].append(stripped)
            
            # Status codes
            if 'status_code=' in stripped:
                patterns["status_codes"].append(stripped)
        
        return patterns
    
    async def _analyze_test_patterns(self, repo_path: str) -> Dict[str, Any]:
        """Analyze testing patterns and conventions."""
        try:
            test_patterns = {
                "test_framework": "unknown",
                "test_structure": [],
                "fixture_usage": False,
                "mock_usage": False,
                "async_tests": False
            }
            
            # Look for test files
            test_files = []
            for root, dirs, files in os.walk(repo_path):
                for file in files:
                    if file.startswith('test_') or 'test' in os.path.basename(root):
                        test_files.append(os.path.join(root, file))
            
            # Analyze test files
            for test_file in test_files:
                try:
                    with open(test_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                        # Detect test framework
                        if 'import pytest' in content:
                            test_patterns["test_framework"] = "pytest"
                        elif 'import unittest' in content:
                            test_patterns["test_framework"] = "unittest"
                        
                        # Check for fixtures
                        if '@pytest.fixture' in content:
                            test_patterns["fixture_usage"] = True
                        
                        # Check for mocking
                        if 'mock' in content.lower() or 'Mock' in content:
                            test_patterns["mock_usage"] = True
                        
                        # Check for async tests
                        if 'async def test_' in content:
                            test_patterns["async_tests"] = True
                
                except Exception as e:
                    logger.debug(f"Could not analyze test file {test_file}: {str(e)}")
                    continue
            
            return test_patterns
            
        except Exception as e:
            logger.error(f"Error analyzing test patterns: {str(e)}")
            return {}
    
    async def _analyze_configuration(self, repo_path: str) -> Dict[str, Any]:
        """Analyze configuration patterns."""
        try:
            config = {
                "config_files": [],
                "environment_variables": [],
                "settings_pattern": "unknown",
                "docker_usage": False
            }
            
            # Check for configuration files
            config_files = [
                '.env', '.env.example', 'config.py', 'settings.py',
                'docker-compose.yml', 'Dockerfile', 'pyproject.toml'
            ]
            
            for config_file in config_files:
                file_path = os.path.join(repo_path, config_file)
                if os.path.exists(file_path):
                    config["config_files"].append(config_file)
                    
                    if config_file in ['docker-compose.yml', 'Dockerfile']:
                        config["docker_usage"] = True
            
            # Check for Pydantic settings
            for root, dirs, files in os.walk(repo_path):
                for file in files:
                    if file.endswith('.py'):
                        file_path = os.path.join(root, file)
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                content = f.read()
                                if 'BaseSettings' in content:
                                    config["settings_pattern"] = "pydantic"
                                elif 'os.environ' in content:
                                    config["settings_pattern"] = "os_environ"
                        except Exception:
                            continue
            
            return config
            
        except Exception as e:
            logger.error(f"Error analyzing configuration: {str(e)}")
            return {}
    
    def get_analysis_summary(self, analysis: Dict[str, Any]) -> str:
        """Generate a human-readable summary of the analysis."""
        try:
            summary_parts = []
            
            # Structure summary
            structure = analysis.get("structure", {})
            py_files = len(structure.get("python_files", []))
            test_files = len(structure.get("test_files", []))
            summary_parts.append(f"Repository contains {py_files} Python files with {test_files} test files")
            
            # Patterns summary
            patterns = analysis.get("patterns", {})
            if patterns.get("async_patterns"):
                summary_parts.append("Uses async/await patterns")
            if patterns.get("type_hints_usage"):
                summary_parts.append("Uses type hints")
            
            # Dependencies summary
            deps = analysis.get("dependencies", {})
            if deps.get("fastapi_version"):
                summary_parts.append(f"Uses {deps['fastapi_version']}")
            
            # API patterns summary
            api = analysis.get("api_patterns", {})
            endpoints = len(api.get("endpoint_patterns", []))
            if endpoints > 0:
                summary_parts.append(f"Has {endpoints} API endpoint patterns")
            
            # Test patterns summary
            tests = analysis.get("test_patterns", {})
            framework = tests.get("test_framework", "unknown")
            if framework != "unknown":
                summary_parts.append(f"Uses {framework} for testing")
            
            return ". ".join(summary_parts) + "."
            
        except Exception as e:
            logger.error(f"Error generating analysis summary: {str(e)}")
            return "Analysis summary unavailable"