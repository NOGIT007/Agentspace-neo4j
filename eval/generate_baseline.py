#!/usr/bin/env python3
"""
Baseline Generation Script for Neo4j Database Agent

This script generates baseline results by running the current agent against
the evaluation dataset. These results can be used for future benchmarking
and comparison against different model versions.

Usage:
    python generate_baseline.py
    python generate_baseline.py --output baseline_results.json
    python generate_baseline.py --model gemini-2.5-flash
"""

import asyncio
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict

# Add the parent directory to sys.path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from neo4j_database_agent.agent import root_agent

# Configure logging
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class BaselineResult:
    """Structure for storing baseline results"""
    query: str
    expected_tool_use: List[Dict[str, Any]]
    actual_tool_use: List[Dict[str, Any]]
    expected_response: str
    actual_response: str
    execution_time_ms: float
    success: bool
    error_message: Optional[str] = None
    model_used: Optional[str] = None
    timestamp: Optional[str] = None

@dataclass
class BaselineReport:
    """Complete baseline report structure"""
    generated_at: str
    model_name: str
    total_queries: int
    successful_queries: int
    failed_queries: int
    total_execution_time_ms: float
    average_execution_time_ms: float
    results: List[BaselineResult]
    summary: Dict[str, Any]

class BaselineGenerator:
    """Generates baseline results for Neo4j Database Agent"""
    
    def __init__(self, eval_data_path: str = None, model_name: str = None):
        """Initialize baseline generator"""
        self.eval_data_path = eval_data_path or self._get_default_eval_path()
        self.model_name = model_name or os.getenv("MODEL_NAME", "gemini-2.5-flash")
        
        # Load evaluation data
        self.eval_data = self._load_eval_data()
        
        logger.info(f"Loaded {len(self.eval_data)} test cases")
        logger.info(f"Using model: {self.model_name}")
    
    def _get_default_eval_path(self) -> str:
        """Get default evaluation data path"""
        return str(Path(__file__).parent / "data" / "baseline_queries.test.json")
    
    def _load_eval_data(self) -> List[Dict[str, Any]]:
        """Load evaluation dataset"""
        try:
            with open(self.eval_data_path, 'r') as f:
                data = json.load(f)
                
                # Handle nested structure with eval_cases
                if isinstance(data, dict) and 'eval_cases' in data:
                    return data['eval_cases']
                # Handle flat array structure
                elif isinstance(data, list):
                    return data
                else:
                    logger.error(f"Unexpected data structure in evaluation file")
                    raise ValueError("Evaluation data must be an array or contain 'eval_cases' key")
                    
        except FileNotFoundError:
            logger.error(f"Evaluation data file not found: {self.eval_data_path}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in evaluation data: {e}")
            raise
    
    async def generate_baseline(self) -> BaselineReport:
        """Generate baseline results by running agent on evaluation dataset"""
        logger.info("Starting baseline generation...")
        
        start_time = time.time()
        results = []
        successful_queries = 0
        failed_queries = 0
        
        for i, test_case in enumerate(self.eval_data, 1):
            logger.info(f"Processing query {i}/{len(self.eval_data)}: {test_case['query'][:50]}...")
            
            result = await self._process_single_query(test_case)
            results.append(result)
            
            if result.success:
                successful_queries += 1
                logger.info(f"✓ Query {i} completed in {result.execution_time_ms:.2f}ms")
            else:
                failed_queries += 1
                logger.error(f"✗ Query {i} failed: {result.error_message}")
        
        total_execution_time = (time.time() - start_time) * 1000
        average_execution_time = total_execution_time / len(self.eval_data)
        
        # Generate summary
        summary = self._generate_summary(results)
        
        # Create report
        report = BaselineReport(
            generated_at=datetime.now().isoformat(),
            model_name=self.model_name,
            total_queries=len(self.eval_data),
            successful_queries=successful_queries,
            failed_queries=failed_queries,
            total_execution_time_ms=total_execution_time,
            average_execution_time_ms=average_execution_time,
            results=results,
            summary=summary
        )
        
        logger.info(f"Baseline generation completed: {successful_queries}/{len(self.eval_data)} queries successful")
        return report
    
    async def _process_single_query(self, test_case: Dict[str, Any]) -> BaselineResult:
        """Process a single query and generate baseline result"""
        query = test_case["query"]
        expected_tool_use = test_case.get("expected_tool_use", [])
        expected_response = test_case.get("reference", "")
        
        start_time = time.time()
        
        try:
            # Import the actual agent directly
            import os
            import sys
            
            # Ensure we're in the project root
            original_cwd = os.getcwd()
            project_root = str(Path(__file__).parent.parent)
            os.chdir(project_root)
            
            # Add project root to Python path
            if project_root not in sys.path:
                sys.path.insert(0, project_root)
            
            # Import and use the actual agent with ADK runner
            from neo4j_database_agent.agent import root_agent
            from google.adk.runners import InMemoryRunner
            from google.genai.types import Part, UserContent
            
            # Create runner with the agent
            runner = InMemoryRunner(agent=root_agent)
            
            # Create session
            session = await runner.session_service.create_session(
                app_name=runner.app_name, user_id="test_user"
            )
            
            # Prepare user content
            content = UserContent(parts=[Part(text=query)])
            
            # Track tool calls and responses
            tool_calls = []
            responses = []
            
            # Use runner.run_async to process the query
            async for event in runner.run_async(
                user_id=session.user_id,
                session_id=session.id,
                new_message=content,
            ):
                if not event.content:
                    continue
                
                # Extract text content
                text_parts = [p.text for p in event.content.parts if p.text]
                for text in text_parts:
                    responses.append(text)
                
                # Extract function calls (tool usage)
                function_calls = [p.function_call for p in event.content.parts if p.function_call]
                for call in function_calls:
                    tool_calls.append({
                        'tool_name': call.name,
                        'tool_input': dict(call.args) if call.args else {}
                    })
            
            execution_time = (time.time() - start_time) * 1000
            
            # Combine response text
            actual_response = ''.join(responses) if responses else "No response generated"
            actual_tool_use = tool_calls
            
            # Restore original working directory
            os.chdir(original_cwd)
            
            return BaselineResult(
                query=query,
                expected_tool_use=expected_tool_use,
                actual_tool_use=actual_tool_use,
                expected_response=expected_response,
                actual_response=actual_response,
                execution_time_ms=execution_time,
                success=True,
                model_used=self.model_name,
                timestamp=datetime.now().isoformat()
            )
            
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            logger.error(f"Query failed: {e}")
            
            # Restore original working directory in case of error
            try:
                os.chdir(original_cwd)
            except:
                pass
            
            return BaselineResult(
                query=query,
                expected_tool_use=expected_tool_use,
                actual_tool_use=[],
                expected_response=expected_response,
                actual_response="",
                execution_time_ms=execution_time,
                success=False,
                error_message=str(e),
                model_used=self.model_name,
                timestamp=datetime.now().isoformat()
            )
    
    def _extract_tool_use_from_events(self, events) -> List[Dict[str, Any]]:
        """Extract tool usage information from agent events"""
        tool_uses = []
        
        for event in events:
            if hasattr(event, 'type') and 'tool' in str(event.type).lower():
                if hasattr(event, 'tool_name') and hasattr(event, 'tool_input'):
                    tool_uses.append({
                        'tool_name': event.tool_name,
                        'tool_input': event.tool_input
                    })
        
        return tool_uses
    
    def _extract_response_text_from_events(self, events) -> str:
        """Extract the response text from agent events"""
        responses = []
        
        for event in events:
            if hasattr(event, 'type') and 'response' in str(event.type).lower():
                if hasattr(event, 'text'):
                    responses.append(event.text)
                elif hasattr(event, 'content'):
                    responses.append(event.content)
            elif hasattr(event, 'text'):
                responses.append(event.text)
        
        return ' '.join(responses) if responses else "No response extracted"
    
    def _generate_summary(self, results: List[BaselineResult]) -> Dict[str, Any]:
        """Generate summary statistics from results"""
        successful_results = [r for r in results if r.success]
        
        if not successful_results:
            return {"error": "No successful queries to analyze"}
        
        execution_times = [r.execution_time_ms for r in successful_results]
        
        return {
            "success_rate": len(successful_results) / len(results) * 100,
            "average_execution_time_ms": sum(execution_times) / len(execution_times),
            "min_execution_time_ms": min(execution_times),
            "max_execution_time_ms": max(execution_times),
            "queries_under_1000ms": len([t for t in execution_times if t < 1000]),
            "queries_under_5000ms": len([t for t in execution_times if t < 5000]),
            "slowest_queries": [
                {
                    "query": r.query[:100] + "..." if len(r.query) > 100 else r.query,
                    "time_ms": r.execution_time_ms
                }
                for r in sorted(successful_results, key=lambda x: x.execution_time_ms, reverse=True)[:5]
            ]
        }
    
    def save_baseline(self, report: BaselineReport, output_path: str = None):
        """Save baseline report to file"""
        if output_path is None:
            output_path = "baseline_results.json"
        
        # Convert report to dict for JSON serialization
        report_dict = asdict(report)
        
        # Ensure output directory exists
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w') as f:
            json.dump(report_dict, f, indent=2, default=str)
        
        logger.info(f"Baseline results saved to: {output_file}")
        
        # Also save a summary file
        summary_path = output_file.with_suffix('.summary.md')
        self._save_summary_markdown(report, summary_path)
        
        return str(output_file)
    
    def _save_summary_markdown(self, report: BaselineReport, path: Path):
        """Save a markdown summary of the baseline results"""
        summary_md = f"""# Baseline Results Summary

**Generated:** {report.generated_at}
**Model:** {report.model_name}
**Total Queries:** {report.total_queries}
**Successful:** {report.successful_queries}
**Failed:** {report.failed_queries}
**Success Rate:** {report.successful_queries/report.total_queries*100:.1f}%

## Performance Metrics

- **Total Execution Time:** {report.total_execution_time_ms:.2f}ms
- **Average Query Time:** {report.average_execution_time_ms:.2f}ms
- **Queries Under 1s:** {report.summary.get('queries_under_1000ms', 0)}/{report.successful_queries}
- **Queries Under 5s:** {report.summary.get('queries_under_5000ms', 0)}/{report.successful_queries}

## Slowest Queries

{chr(10).join(f"- {q['query']} ({q['time_ms']:.2f}ms)" for q in report.summary.get('slowest_queries', []))}

## Usage

Use this baseline for future comparisons:

```bash
# Compare against this baseline
python generate_baseline.py --baseline {path.with_suffix('.json').name}

# Run evaluation
pytest eval/test_eval.py
```
"""
        
        with open(path, 'w') as f:
            f.write(summary_md)
        
        logger.info(f"Summary saved to: {path}")

async def main():
    """Main entry point for CLI execution"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate baseline results for Neo4j Database Agent")
    parser.add_argument(
        "--eval-data", 
        type=str, 
        help="Path to evaluation dataset file"
    )
    parser.add_argument(
        "--output", 
        type=str, 
        help="Output file path for baseline results"
    )
    parser.add_argument(
        "--model", 
        type=str, 
        help="Model name to use for baseline generation"
    )
    
    args = parser.parse_args()
    
    # Setup environment
    load_dotenv()
    
    # Check required environment variables
    required_vars = ['NEO4J_URI', 'NEO4J_USERNAME', 'NEO4J_PASSWORD', 'GOOGLE_CLOUD_PROJECT']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        logger.error(f"Missing required environment variables: {missing_vars}")
        sys.exit(1)
    
    # Create generator
    generator = BaselineGenerator(
        eval_data_path=args.eval_data,
        model_name=args.model
    )
    
    # Generate baseline
    try:
        report = await generator.generate_baseline()
        output_path = generator.save_baseline(report, args.output)
        
        print(f"✅ Baseline generation completed successfully!")
        print(f"📄 Results saved to: {output_path}")
        print(f"📊 Success rate: {report.successful_queries}/{report.total_queries} ({report.successful_queries/report.total_queries*100:.1f}%)")
        print(f"⏱️  Average query time: {report.average_execution_time_ms:.2f}ms")
        
        # Show summary
        print("\n" + "="*60)
        print("BASELINE SUMMARY")
        print("="*60)
        print(f"Model: {report.model_name}")
        print(f"Total queries: {report.total_queries}")
        print(f"Successful: {report.successful_queries}")
        print(f"Failed: {report.failed_queries}")
        print(f"Success rate: {report.successful_queries/report.total_queries*100:.1f}%")
        
        if report.summary.get('slowest_queries'):
            print("\nSlowest queries:")
            for q in report.summary['slowest_queries'][:3]:
                print(f"  - {q['query']} ({q['time_ms']:.2f}ms)")
        
        sys.exit(0)
        
    except Exception as e:
        logger.error(f"Baseline generation failed: {e}")
        print("❌ Baseline generation FAILED")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())