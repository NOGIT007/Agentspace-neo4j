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
# Run local agent tests
python test_agent_local.py
```

## Architecture Overview

### Core Components

1. **agents/agent.py** - Main agent implementation
   - `root_agent`: LlmAgent instance with Neo4j querying capabilities
   - Tools: `check_schema_cache`, `get_neo4j_schema`, `execute_cypher_query`, `refresh_neo4j_schema`
   - Implements schema caching for performance optimization
   - Security: Only allows read-only operations (blocks CREATE, MERGE, SET, DELETE)

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

## Instructions for Claude
- Follow the requirements specified in docs/doc.md
- Use Google ADK patterns
- Follow MCP Neo4j integration