#!/usr/bin/env python3
"""
Test script for AI workflow validation.

This script tests the AI-powered coding workflow to ensure
all components are working together correctly.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from coding_agent.models.requests import CodingRequest
from coding_agent.core.workflow_engine import WorkflowEngine


async def test_ai_workflow():
    """Test the AI-powered coding workflow."""
    
    print("🤖 Testing AI-Powered Coding Workflow")
    print("=" * 50)
    
    # Check environment variables
    required_vars = ["OPENAI_API_KEY", "GITHUB_TOKEN", "GITHUB_REPOSITORY"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"⚠️  Missing environment variables: {', '.join(missing_vars)}")
        print("   This test will use simulated responses where possible")
        print()
    
    # Create workflow engine
    try:
        engine = WorkflowEngine()
        print("✅ Workflow engine initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize workflow engine: {e}")
        return
    
    # Create test request
    test_request = CodingRequest(
        requirements="Add a simple /api/v1/health endpoint that returns service status and uptime",
        target_service="market-predictor",
        priority="medium",
        context="This endpoint will be used by monitoring systems for health checks"
    )
    
    print(f"📝 Test Requirements: {test_request.requirements}")
    print()
    
    # Start coding workflow
    try:
        print("🚀 Starting AI coding workflow...")
        response = await engine.start_coding_workflow(test_request)
        
        print(f"✅ Workflow started successfully!")
        print(f"   Task ID: {response.task_id}")
        print(f"   Branch Name: {response.branch_name}")
        print(f"   Estimated Duration: {response.estimated_duration}")
        print(f"   Status: {response.status}")
        print()
        
        # Monitor progress
        print("📊 Monitoring workflow progress...")
        
        for i in range(30):  # Monitor for up to 30 seconds
            await asyncio.sleep(1)
            
            status = await engine.get_task_status(response.task_id)
            if status:
                print(f"   Progress: {status.progress_percentage}% - {status.current_step}")
                
                if status.status.value in ["completed", "failed", "cancelled"]:
                    break
        
        # Final status
        final_status = await engine.get_task_status(response.task_id)
        if final_status:
            print()
            print("🏁 Final Status:")
            print(f"   Status: {final_status.status.value}")
            print(f"   Progress: {final_status.progress_percentage}%")
            print(f"   Files Modified: {len(final_status.code_changes)}")
            print(f"   Test Results: {len(final_status.test_results)}")
            
            if final_status.pr_url:
                print(f"   PR URL: {final_status.pr_url}")
            
            if final_status.error_message:
                print(f"   Error: {final_status.error_message}")
            
            # Show workflow steps
            print("\n📋 Workflow Steps:")
            for step in final_status.workflow_steps:
                status_icon = "✅" if step.status == "completed" else "❌" if step.status == "failed" else "⏳"
                print(f"   {status_icon} {step.step_name}")
                if step.duration_seconds:
                    print(f"      Duration: {step.duration_seconds:.1f}s")
                if step.error_message:
                    print(f"      Error: {step.error_message}")
            
            # Show code changes
            if final_status.code_changes:
                print("\n📁 Code Changes:")
                for change in final_status.code_changes:
                    print(f"   📄 {change.file_path} ({change.change_type})")
                    print(f"      +{change.lines_added} -{change.lines_removed}")
                    print(f"      {change.description}")
            
            # Success evaluation
            if final_status.status.value == "completed":
                print("\n🎉 AI Coding Workflow Test PASSED!")
                print("   The AI successfully converted requirements into code!")
            elif final_status.status.value == "failed":
                print("\n❌ AI Coding Workflow Test FAILED")
                print(f"   Error: {final_status.error_message}")
            else:
                print(f"\n⏸️  Workflow is still running (status: {final_status.status.value})")
        
    except Exception as e:
        print(f"❌ Workflow test failed: {e}")
        import traceback
        traceback.print_exc()


async def test_individual_components():
    """Test individual AI components."""
    
    print("\n🧪 Testing Individual AI Components")
    print("=" * 50)
    
    # Test AI agent initialization
    try:
        from coding_agent.agents.coding_agents import CodingAgentOrchestrator
        orchestrator = CodingAgentOrchestrator()
        print("✅ AI Agent Orchestrator initialized")
        
        # Test prompt registry
        from coding_agent.config.prompts import PromptRegistry
        system_prompts = PromptRegistry.get_system_prompts()
        print(f"✅ Prompt Registry loaded ({len(system_prompts)} prompts)")
        
        # Test services
        from coding_agent.services.git_service import GitService
        from coding_agent.services.code_analysis import CodeAnalysisService
        
        git_service = GitService()
        code_analyzer = CodeAnalysisService()
        
        print("✅ Git Service initialized")
        print("✅ Code Analysis Service initialized")
        
        # Test helper functions
        commit_msg = git_service.generate_commit_message(
            requirements="Test requirement",
            files_changed=["test.py"],
            implementation_type="feature"
        )
        print(f"✅ Commit message generation: {commit_msg[:50]}...")
        
    except Exception as e:
        print(f"❌ Component test failed: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """Main test function."""
    
    print("🚀 Coding AI Agent - Phase 1.2 Integration Test")
    print("🎯 Testing AI-Powered Autonomous Software Development")
    print()
    
    # Test individual components first
    await test_individual_components()
    
    # Test complete workflow
    await test_ai_workflow()
    
    print("\n" + "=" * 50)
    print("🔬 Test Summary:")
    print("   - AI Agent Integration: Component initialization")
    print("   - Workflow Engine: Complete development workflow") 
    print("   - Git Operations: Branch management and PR creation")
    print("   - Code Generation: AI-powered code creation")
    print()
    print("🎉 Phase 1.2 AI Integration Testing Complete!")


if __name__ == "__main__":
    asyncio.run(main())