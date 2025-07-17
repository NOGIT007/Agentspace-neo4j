#!/usr/bin/env python3
"""
Neo4j Database Agent Evaluation Script
Uses Google ADK AgentEvaluator for standardized evaluation
"""

import os
import sys
import asyncio
import pytest
import logging
from pathlib import Path
from dotenv import load_dotenv

# Configure logging early
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add the parent directory to sys.path to import the agent
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from google.adk.evaluation.agent_evaluator import AgentEvaluator
    # Try to import EvalResult, but handle if it's not available
    try:
        from google.adk.evaluation.eval_result import EvalResult
    except ImportError:
        # If EvalResult is not available, we'll work with generic result type
        EvalResult = object
        logger.warning("EvalResult not available, using generic result type")
except ImportError as e:
    print(f"Google ADK evaluation framework not available: {e}")
    print("Please ensure google-adk is installed with evaluation dependencies")
    sys.exit(1)

# Load environment variables
load_dotenv()

class Neo4jAgentEvaluator:
    """Evaluation wrapper for Neo4j Database Agent"""
    
    def __init__(self, eval_data_path: str = None, config_path: str = None):
        """Initialize evaluator with data and config paths"""
        self.eval_data_path = eval_data_path or self._get_default_eval_path()
        self.config_path = config_path or self._get_default_config_path()
        
        # Ensure paths exist
        if not os.path.exists(self.eval_data_path):
            raise FileNotFoundError(f"Evaluation data file not found: {self.eval_data_path}")
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"Config file not found: {self.config_path}")
            
        logger.info(f"Evaluation data: {self.eval_data_path}")
        logger.info(f"Config file: {self.config_path}")
    
    def _get_default_eval_path(self) -> str:
        """Get default evaluation data path"""
        return str(Path(__file__).parent / "data" / "baseline_queries.test.json")
    
    def _get_default_config_path(self) -> str:
        """Get default config path"""
        return str(Path(__file__).parent / "data" / "test_config.json")
    
    async def run_evaluation(self, num_runs: int = 1):
        """Run evaluation using Google ADK AgentEvaluator"""
        logger.info(f"Starting evaluation with {num_runs} runs...")
        
        try:
            # Run evaluation using ADK framework
            result = await AgentEvaluator.evaluate(
                agent_module="neo4j_database_agent",
                eval_dataset_file_path_or_dir=self.eval_data_path,
                config_file_path=self.config_path,
                num_runs=num_runs,
            )
            
            logger.info("Evaluation completed successfully")
            return result
            
        except Exception as e:
            logger.error(f"Evaluation failed: {e}")
            raise
    
    def print_results(self, result):
        """Print evaluation results in a readable format"""
        print("\n" + "="*60)
        print("NEO4J DATABASE AGENT EVALUATION RESULTS")
        print("="*60)
        
        if hasattr(result, 'overall_score'):
            print(f"Overall Score: {result.overall_score:.3f}")
        
        if hasattr(result, 'tool_trajectory_avg_score'):
            print(f"Tool Trajectory Score: {result.tool_trajectory_avg_score:.3f}")
        
        if hasattr(result, 'response_match_score'):
            print(f"Response Match Score: {result.response_match_score:.3f}")
        
        if hasattr(result, 'individual_results'):
            print(f"\nIndividual Test Results: {len(result.individual_results)} tests")
            
            # Show summary of pass/fail
            passed = sum(1 for r in result.individual_results if getattr(r, 'passed', False))
            failed = len(result.individual_results) - passed
            print(f"Passed: {passed}, Failed: {failed}")
            
            # Show failed tests if any
            if failed > 0:
                print("\nFailed Tests:")
                for i, test_result in enumerate(result.individual_results):
                    if not getattr(test_result, 'passed', True):
                        print(f"  {i+1}. {getattr(test_result, 'query', 'Unknown query')}")
                        if hasattr(test_result, 'error_message'):
                            print(f"      Error: {test_result.error_message}")
        
        print("\n" + "="*60)

# Pytest fixtures and test functions
@pytest.fixture(scope="session", autouse=True)
def setup_environment():
    """Setup environment for evaluation"""
    # Ensure required environment variables are set
    required_vars = ['NEO4J_URI', 'NEO4J_USERNAME', 'NEO4J_PASSWORD', 'GOOGLE_CLOUD_PROJECT']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        pytest.skip(f"Missing required environment variables: {missing_vars}")
    
    logger.info("Environment setup complete")

@pytest.mark.asyncio
async def test_baseline_evaluation():
    """Test baseline evaluation dataset"""
    evaluator = Neo4jAgentEvaluator()
    result = await evaluator.run_evaluation(num_runs=1)
    
    # Print results
    evaluator.print_results(result)
    
    # Basic assertions
    assert result is not None, "Evaluation should return a result"
    
    # Check if we have reasonable scores (adjust thresholds as needed)
    if hasattr(result, 'overall_score'):
        assert result.overall_score >= 0.0, "Overall score should be non-negative"
        logger.info(f"Overall score: {result.overall_score}")
    
    if hasattr(result, 'tool_trajectory_avg_score'):
        assert result.tool_trajectory_avg_score >= 0.0, "Tool trajectory score should be non-negative"
        logger.info(f"Tool trajectory score: {result.tool_trajectory_avg_score}")
    
    if hasattr(result, 'response_match_score'):
        assert result.response_match_score >= 0.0, "Response match score should be non-negative"
        logger.info(f"Response match score: {result.response_match_score}")

@pytest.mark.asyncio
async def test_evaluation_with_multiple_runs():
    """Test evaluation with multiple runs for consistency"""
    evaluator = Neo4jAgentEvaluator()
    result = await evaluator.run_evaluation(num_runs=2)
    
    # Print results
    evaluator.print_results(result)
    
    # Check that multiple runs complete successfully
    assert result is not None, "Multiple run evaluation should return a result"

# CLI entry point
async def main():
    """Main entry point for CLI execution"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Neo4j Database Agent Evaluation")
    parser.add_argument(
        "--eval-data", 
        type=str, 
        help="Path to evaluation dataset file"
    )
    parser.add_argument(
        "--config", 
        type=str, 
        help="Path to evaluation config file"
    )
    parser.add_argument(
        "--num-runs", 
        type=int, 
        default=1, 
        help="Number of evaluation runs"
    )
    
    args = parser.parse_args()
    
    # Setup environment
    load_dotenv()
    
    # Create evaluator
    evaluator = Neo4jAgentEvaluator(
        eval_data_path=args.eval_data,
        config_path=args.config
    )
    
    # Run evaluation
    try:
        result = await evaluator.run_evaluation(num_runs=args.num_runs)
        evaluator.print_results(result)
        
        # Exit with appropriate code
        if hasattr(result, 'overall_score') and result.overall_score > 0.5:
            print("✅ Evaluation PASSED")
            sys.exit(0)
        else:
            print("❌ Evaluation needs improvement")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Evaluation failed: {e}")
        print("❌ Evaluation FAILED")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())