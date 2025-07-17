# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Neo4j ADK (Agent Development Kit) agent that enables natural language querying of Neo4j databases using Google's Gemini models. The agent converts natural language queries into Cypher queries and retrieves data from Neo4j databases.

## Development Commands

### Setup and Installation
```bash
# Install dependencies using uv (required)
./install.sh

# Activate virtual environment
source .venv/bin/activate
```

### Running the Application
```bash
# Start the Flask web UI for deployment management
./start.sh
# Or directly:
uv run python app.py

# Start ADK web interface for local agent testing
adk web

# Test agent locally before deployment
python test_agent_local.py
```

### Testing
```bash
# Test agent locally with ADK web interface
adk web

# Run evaluation tests
cd eval
python generate_baseline.py

# Run full evaluation
adk eval neo4j_database_agent data/baseline_queries.test.json --config_file_path data/test_config.json
```

## Architecture Overview

### Core Components

1. **neo4j_database_agent/agent.py** - Main agent implementation
   - `root_agent`: Agent instance with Neo4j querying capabilities
   - Tools: `check_schema_cache`, `get_neo4j_schema`, `execute_cypher_query`, `refresh_neo4j_schema`
   - Implements schema caching for performance optimization
   - Security: Only allows read-only operations (blocks CREATE, MERGE, SET, DELETE)
   - Environment: Uses `load_dotenv(override=True)` to prioritize .env over shell variables

2. **app.py** - Flask application for deployment management
   - Web UI for deploying agents to Vertex AI Agent Engine
   - Endpoints for deployment (`/deploy`), testing (`/test`), and Agentspace registration
   - Handles agent lifecycle: deploy → test → register to Agentspace → list/delete

3. **Environment Configuration**
   - Requires `.env` file with Google Cloud and Neo4j credentials
   - Key variables: `GOOGLE_CLOUD_PROJECT`, `NEO4J_URI`, `NEO4J_USERNAME`, `NEO4J_PASSWORD`

### Agent Workflow

The agent follows a strict workflow for optimal performance:
1. Check schema cache first (`check_schema_cache`)
2. If not cached, retrieve schema (`get_neo4j_schema`)
3. Generate Cypher query based on user request and schema
4. Execute query (`execute_cypher_query`)
5. Return formatted results

### Deployment Architecture

- Deploys to Vertex AI Agent Engine using `vertexai.agent_engines`
- Uses `google-adk` framework
- Supports registration to Agentspace for integration
- Storage bucket required for deployment artifacts

## Key Technical Details

- Python 3.11+ required
- Uses `uv` package manager for dependency management
- Flask web UI on port 5000
- Neo4j driver with connection pooling
- Schema caching implemented with in-memory dictionary
- Date/datetime objects automatically converted to strings for JSON serialization

## Dependencies

Main dependencies from pyproject.toml:
- `google-adk>=0.1.0`
- `google-cloud-aiplatform>=1.40.0`
- `neo4j>=5.0.0`
- `flask>=2.3.0`
- `python-dotenv>=1.0.0`

## Security Considerations

- Agent only performs read-only operations
- Write operations (CREATE, MERGE, SET, DELETE) are explicitly blocked in `execute_cypher_query`
- Credentials stored in `.env` file (not committed to git)

## Documentation
- **Project Requirements**: Please read `docs/doc.md` for detailed technical specifications and requirements

## Google ADK Evaluation

### Evaluation Structure
Following Google ADK patterns, evaluation is organized in:
```
eval/
├── data/
│   ├── test_config.json          # Evaluation criteria and scoring thresholds
│   └── baseline_queries.test.json # Test dataset with 20 comprehensive test cases
├── baseline_results.json         # Performance baseline (100% success rate)
├── baseline_results.summary.md   # Human-readable performance summary
├── eval.md                       # Simple evaluation guide
├── generate_baseline.py          # Baseline generation script
└── test_eval.py                  # Evaluation script using AgentEvaluator
```

### Evaluation Commands
```bash
# Run evaluation using ADK CLI
adk eval neo4j_database_agent eval/data/baseline_queries.test.json --config_file_path eval/data/test_config.json

# Run evaluation using pytest
pytest eval/test_eval.py

# Generate baseline results
python generate_baseline.py
```

### Evaluation Dataset Format
Each test case follows ADK standard format:
```json
{
  "query": "User input text",
  "expected_tool_use": [
    {
      "tool_name": "execute_cypher_query",
      "tool_input": {"query": "MATCH (n) RETURN count(n)"}
    }
  ],
  "reference": "Expected response text"
}
```

### Baseline Generation
- Run `generate_baseline.py` to create initial baseline results
- Results are compared against current Gemini model performance
- Enables benchmarking against future model updates

### Google ADK Samples Reference
Local ADK samples available at: `/Users/kennetkusk/code/google/adk-samples/python`
- Contains evaluation patterns and best practices
- Reference implementations for various agent types
- MCP integration examples

## Instructions for Claude
- Follow the requirements specified in docs/doc.md
- Use Google ADK patterns
- Follow MCP Neo4j integration
- Use ADK evaluation framework for testing