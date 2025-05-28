"""
LangChain AI Agents for Autonomous Code Generation.

This module implements the core AI agents that power the autonomous coding
workflow: Planner, Coder, and Tester agents using LangChain framework.
"""

import logging
from typing import Dict, Any, Optional, List
import json
import asyncio

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.callbacks.base import BaseCallbackHandler

from ..config.settings import get_settings
from ..config.prompts import PromptRegistry


logger = logging.getLogger(__name__)


class CodingCallbackHandler(BaseCallbackHandler):
    """Custom callback handler for tracking AI agent operations."""
    
    def __init__(self):
        self.tokens_used = 0
        self.requests_made = 0
        self.errors = []
    
    def on_llm_start(self, serialized: Dict[str, Any], prompts: List[str], **kwargs: Any) -> None:
        """Called when LLM starts."""
        self.requests_made += 1
        logger.debug(f"LLM request started. Total requests: {self.requests_made}")
    
    def on_llm_end(self, response, **kwargs: Any) -> None:
        """Called when LLM ends."""
        # Track token usage if available
        if hasattr(response, 'llm_output') and response.llm_output:
            tokens = response.llm_output.get('token_usage', {})
            if tokens:
                self.tokens_used += tokens.get('total_tokens', 0)
        logger.debug(f"LLM request completed. Total tokens: {self.tokens_used}")
    
    def on_llm_error(self, error: Exception, **kwargs: Any) -> None:
        """Called when LLM errors."""
        self.errors.append(str(error))
        logger.error(f"LLM error: {error}")


class PlannerAgent:
    """
    AI agent responsible for analyzing requirements and creating implementation plans.
    
    This agent takes natural language requirements and converts them into
    detailed, actionable implementation plans that guide the coding process.
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.callback_handler = CodingCallbackHandler()
        
        # Initialize the LLM
        self.llm = ChatOpenAI(
            model_name=self.settings.llm_model,
            temperature=self.settings.llm_temperature,
            max_tokens=self.settings.llm_max_tokens,
            openai_api_key=self.settings.openai_api_key,
            callbacks=[self.callback_handler]
        )
        
        # Get prompts
        self.prompt_template = PromptRegistry.get_planner_prompt()
        self.system_prompt = PromptRegistry.get_system_prompts()["planner"]
    
    async def analyze_requirements(
        self,
        requirements: str,
        target_service: str,
        context: Optional[str] = None,
        repo_structure: Optional[Dict[str, Any]] = None,
        existing_patterns: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Analyze coding requirements and create implementation plan.
        
        Args:
            requirements: Natural language coding requirements
            target_service: Target service name
            context: Additional context for the requirements
            repo_structure: Repository structure information
            existing_patterns: Existing code patterns and conventions
            
        Returns:
            Detailed implementation plan as a dictionary
        """
        try:
            logger.info(f"Planning implementation for: {requirements[:100]}...")
            
            # Prepare input data
            input_data = {
                "requirements": requirements,
                "target_service": target_service,
                "context": context or "No additional context provided",
                "repo_structure": json.dumps(repo_structure or {}, indent=2),
                "existing_patterns": json.dumps(existing_patterns or {}, indent=2)
            }
            
            # Format the prompt
            human_prompt = self.prompt_template.format(**input_data)
            
            # Create messages
            messages = [
                SystemMessage(content=self.system_prompt),
                HumanMessage(content=human_prompt)
            ]
            
            # Get AI response
            response = await asyncio.get_event_loop().run_in_executor(
                None, lambda: self.llm.invoke(messages)
            )
            
            # Parse the response
            plan = self._parse_plan_response(response.content)
            
            logger.info("Implementation plan created successfully")
            return plan
            
        except Exception as e:
            logger.error(f"Error in requirements analysis: {str(e)}")
            raise Exception(f"Failed to analyze requirements: {str(e)}")
    
    def _parse_plan_response(self, response_content: str) -> Dict[str, Any]:
        """Parse the AI response into a structured plan."""
        try:
            # Try to extract JSON from the response
            if "```json" in response_content:
                json_start = response_content.find("```json") + 7
                json_end = response_content.find("```", json_start)
                json_content = response_content[json_start:json_end].strip()
                return json.loads(json_content)
            
            # If no JSON found, create a structured plan from the text
            return {
                "requirement_analysis": {
                    "description": "Requirements analyzed",
                    "complexity": "medium",
                    "tasks": []
                },
                "technical_design": {
                    "approach": "Implementation approach defined",
                    "components": [],
                    "endpoints": []
                },
                "implementation_plan": {
                    "files_to_modify": [],
                    "files_to_create": [],
                    "dependencies": [],
                    "sequence": []
                },
                "testing_strategy": {
                    "unit_tests": True,
                    "integration_tests": True,
                    "test_files": []
                },
                "risk_assessment": {
                    "risks": [],
                    "mitigation": []
                },
                "raw_response": response_content
            }
            
        except json.JSONDecodeError:
            logger.warning("Could not parse JSON from planner response, using fallback structure")
            return {
                "requirement_analysis": {"description": "Requirements analyzed"},
                "implementation_plan": {"files_to_modify": [], "files_to_create": []},
                "testing_strategy": {"unit_tests": True},
                "raw_response": response_content
            }


class CoderAgent:
    """
    AI agent responsible for generating production-quality code.
    
    This agent takes implementation plans and generates working FastAPI
    code that follows best practices and existing patterns.
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.callback_handler = CodingCallbackHandler()
        
        # Initialize the LLM
        self.llm = ChatOpenAI(
            model_name=self.settings.llm_model,
            temperature=self.settings.llm_temperature,
            max_tokens=self.settings.llm_max_tokens,
            openai_api_key=self.settings.openai_api_key,
            callbacks=[self.callback_handler]
        )
        
        # Get prompts
        self.prompt_template = PromptRegistry.get_coder_prompt()
        self.system_prompt = PromptRegistry.get_system_prompts()["coder"]
    
    async def generate_code(
        self,
        implementation_plan: Dict[str, Any],
        target_file: str,
        changes_required: str,
        target_service: str,
        existing_patterns: Optional[Dict[str, Any]] = None,
        repo_structure: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate production-quality code based on implementation plan.
        
        Args:
            implementation_plan: Detailed implementation plan from planner
            target_file: File to generate/modify
            changes_required: Specific changes needed for this file
            target_service: Target service name
            existing_patterns: Existing code patterns to follow
            repo_structure: Repository structure information
            
        Returns:
            Generated code as a string
        """
        try:
            logger.info(f"Generating code for file: {target_file}")
            
            # Prepare input data
            input_data = {
                "implementation_plan": json.dumps(implementation_plan, indent=2),
                "target_file": target_file,
                "changes_required": changes_required,
                "target_service": target_service,
                "existing_patterns": json.dumps(existing_patterns or {}, indent=2),
                "repo_structure": json.dumps(repo_structure or {}, indent=2)
            }
            
            # Format the prompt
            human_prompt = self.prompt_template.format(**input_data)
            
            # Create messages
            messages = [
                SystemMessage(content=self.system_prompt),
                HumanMessage(content=human_prompt)
            ]
            
            # Get AI response
            response = await asyncio.get_event_loop().run_in_executor(
                None, lambda: self.llm.invoke(messages)
            )
            
            # Extract code from response
            generated_code = self._extract_code_from_response(response.content)
            
            logger.info(f"Code generated successfully for {target_file}")
            return generated_code
            
        except Exception as e:
            logger.error(f"Error in code generation: {str(e)}")
            raise Exception(f"Failed to generate code: {str(e)}")
    
    def _extract_code_from_response(self, response_content: str) -> str:
        """Extract code from the AI response."""
        # Look for code blocks
        if "```python" in response_content:
            code_start = response_content.find("```python") + 9
            code_end = response_content.find("```", code_start)
            return response_content[code_start:code_end].strip()
        elif "```" in response_content:
            code_start = response_content.find("```") + 3
            code_end = response_content.find("```", code_start)
            return response_content[code_start:code_end].strip()
        else:
            # If no code blocks found, return the whole response
            return response_content.strip()


class TesterAgent:
    """
    AI agent responsible for generating comprehensive test suites.
    
    This agent creates unit tests, integration tests, and API tests
    for the generated code to ensure quality and reliability.
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.callback_handler = CodingCallbackHandler()
        
        # Initialize the LLM
        self.llm = ChatOpenAI(
            model_name=self.settings.llm_model,
            temperature=self.settings.llm_temperature,
            max_tokens=self.settings.llm_max_tokens,
            openai_api_key=self.settings.openai_api_key,
            callbacks=[self.callback_handler]
        )
        
        # Get prompts
        self.prompt_template = PromptRegistry.get_tester_prompt()
        self.system_prompt = PromptRegistry.get_system_prompts()["tester"]
    
    async def generate_tests(
        self,
        code_content: str,
        feature_description: str,
        target_service: str,
        api_endpoints: Optional[List[str]] = None
    ) -> str:
        """
        Generate comprehensive test suite for the provided code.
        
        Args:
            code_content: The code to generate tests for
            feature_description: Description of the feature being tested
            target_service: Target service name
            api_endpoints: List of API endpoints to test
            
        Returns:
            Generated test code as a string
        """
        try:
            logger.info(f"Generating tests for feature: {feature_description}")
            
            # Prepare input data
            input_data = {
                "code_content": code_content,
                "feature_description": feature_description,
                "target_service": target_service,
                "api_endpoints": json.dumps(api_endpoints or [], indent=2)
            }
            
            # Format the prompt
            human_prompt = self.prompt_template.format(**input_data)
            
            # Create messages
            messages = [
                SystemMessage(content=self.system_prompt),
                HumanMessage(content=human_prompt)
            ]
            
            # Get AI response
            response = await asyncio.get_event_loop().run_in_executor(
                None, lambda: self.llm.invoke(messages)
            )
            
            # Extract test code from response
            test_code = self._extract_code_from_response(response.content)
            
            logger.info("Test suite generated successfully")
            return test_code
            
        except Exception as e:
            logger.error(f"Error in test generation: {str(e)}")
            raise Exception(f"Failed to generate tests: {str(e)}")
    
    def _extract_code_from_response(self, response_content: str) -> str:
        """Extract test code from the AI response."""
        # Look for code blocks
        if "```python" in response_content:
            code_start = response_content.find("```python") + 9
            code_end = response_content.find("```", code_start)
            return response_content[code_start:code_end].strip()
        elif "```" in response_content:
            code_start = response_content.find("```") + 3
            code_end = response_content.find("```", code_start)
            return response_content[code_start:code_end].strip()
        else:
            # If no code blocks found, return the whole response
            return response_content.strip()


class CodingAgentOrchestrator:
    """
    Orchestrates the interaction between different AI agents.
    
    This class manages the workflow between Planner, Coder, and Tester
    agents to create a complete implementation from requirements.
    """
    
    def __init__(self):
        self.planner = PlannerAgent()
        self.coder = CoderAgent()
        self.tester = TesterAgent()
        
        logger.info("Coding agent orchestrator initialized")
    
    async def create_implementation(
        self,
        requirements: str,
        target_service: str,
        context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a complete implementation from requirements.
        
        Args:
            requirements: Natural language requirements
            target_service: Target service name
            context: Additional context
            
        Returns:
            Complete implementation with code and tests
        """
        try:
            logger.info("Starting complete implementation workflow")
            
            # Step 1: Analyze requirements and create plan
            plan = await self.planner.analyze_requirements(
                requirements=requirements,
                target_service=target_service,
                context=context
            )
            
            # Step 2: Generate code based on plan
            implementation_files = {}
            test_files = {}
            
            # Get files to create/modify from plan
            files_to_create = plan.get("implementation_plan", {}).get("files_to_create", [])
            files_to_modify = plan.get("implementation_plan", {}).get("files_to_modify", [])
            
            # Generate code for each file
            for file_info in files_to_create + files_to_modify:
                if isinstance(file_info, dict):
                    file_path = file_info.get("path", "")
                    changes = file_info.get("changes", "")
                elif isinstance(file_info, str):
                    file_path = file_info
                    changes = "Create new file based on requirements"
                else:
                    continue
                
                if file_path and not file_path.startswith("test_"):
                    # Generate main code
                    code = await self.coder.generate_code(
                        implementation_plan=plan,
                        target_file=file_path,
                        changes_required=changes,
                        target_service=target_service
                    )
                    implementation_files[file_path] = code
                    
                    # Generate tests for this code
                    test_file = f"test_{file_path.replace('/', '_').replace('.py', '')}.py"
                    test_code = await self.tester.generate_tests(
                        code_content=code,
                        feature_description=requirements,
                        target_service=target_service
                    )
                    test_files[test_file] = test_code
            
            result = {
                "plan": plan,
                "implementation_files": implementation_files,
                "test_files": test_files,
                "success": True
            }
            
            logger.info("Complete implementation workflow finished successfully")
            return result
            
        except Exception as e:
            logger.error(f"Error in implementation workflow: {str(e)}")
            return {
                "plan": {},
                "implementation_files": {},
                "test_files": {},
                "success": False,
                "error": str(e)
            }
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get usage statistics from all agents."""
        return {
            "planner": {
                "requests": self.planner.callback_handler.requests_made,
                "tokens": self.planner.callback_handler.tokens_used,
                "errors": len(self.planner.callback_handler.errors)
            },
            "coder": {
                "requests": self.coder.callback_handler.requests_made,
                "tokens": self.coder.callback_handler.tokens_used,
                "errors": len(self.coder.callback_handler.errors)
            },
            "tester": {
                "requests": self.tester.callback_handler.requests_made,
                "tokens": self.tester.callback_handler.tokens_used,
                "errors": len(self.tester.callback_handler.errors)
            }
        }