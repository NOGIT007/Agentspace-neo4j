# Neo4j Database Agent

A Google Agent Development Kit (ADK) agent that enables secure natural language querying of Neo4j databases. This agent uses Gemini models to understand user queries and automatically generates appropriate Cypher queries to retrieve data from your Neo4j database.

## 🚀 Features

### Core Capabilities
- 🗣️ **Natural Language Processing**: Convert natural language to Cypher queries
- 📊 **Automatic Schema Discovery**: Smart database schema caching and discovery
- 🔒 **Security Controls**: Advanced security with destructive operation blocking
- 🌐 **Neo4j Integration**: Works with Neo4j AuraDB and self-hosted instances
- ⚡ **Performance Optimized**: Schema caching for improved response times
- 🚀 **Cloud Deployment**: Deploy to Vertex AI Agent Engine

### Enhanced Query Support
- 📅 **Time-based Queries**: Year/month/quarter comparisons, date ranges
- 📈 **Advanced Aggregations**: Count, sum, average, min, max with GROUP BY
- 💰 **Financial Calculations**: Revenue totals, running totals, percentages
- 🔗 **Relationship Analysis**: Customer orders, product categories, connections
- 📋 **Smart Formatting**: Markdown tables for multi-row, key-value for single results
- 🧧 **Invoice Analytics**: Robust invoice counting with correct property handling

### Security Features
- 🛡️ **Query Intent Analysis**: Fast detection of destructive operations
- 🚫 **Write Operation Blocking**: Prevents CREATE, UPDATE, DELETE operations
- 💡 **Helpful Suggestions**: Reformulation guidance for blocked queries
- ⚡ **Fast Security Check**: Fast security validation without performance impact

## Prerequisites

- Python 3.11 or higher
- Google Cloud Project with Vertex AI enabled
- Neo4j database (AuraDB or self-hosted)
- `uv` package manager installed

## Installation

1. Clone the repository:
```bash
git clone https://github.com/your-username/neo4j-database-agent.git
cd neo4j-database-agent
```

2. Run the installation script:
```bash
./install.sh
```

3. Configure your environment variables by creating a `.env` file:
```bash
# Google Cloud Configuration
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_CLOUD_LOCATION=europe-west1
MODEL_NAME=gemini-2.5-flash

# Neo4j Configuration
NEO4J_URI=neo4j+s://your-instance.endpoints.neo4j.io
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your-password
NEO4J_DATABASE=neo4j
```

## Usage

### Local Testing with ADK Web Interface

```bash
# Start the agent locally for testing
adk web
```

Navigate to http://localhost:8080 to interact with the agent.

### Web UI for Deployment Management

1. Start the Flask application:
```bash
./start.sh
```

2. Navigate to http://localhost:5001

3. Use the web interface to:
   - Deploy agent to Vertex AI Agent Engine
   - Test deployed agent
   - Register to Agentspace
   - Manage deployed agents

## Example Queries

The agent supports a wide range of natural language queries:

### Basic Queries
- "How many customers do we have?"
- "Show me all active subscriptions" 
- "Count all the invoices per year"

### Time-based Analysis
- "Show invoices by year" → Returns markdown table
- "Compare quarterly revenue" → Year/quarter breakdown
- "Monthly sales from last year" → Time period filtering

### Financial & Business Analytics
- "What's our total monthly recurring revenue?"
- "Find customers with the highest invoice amounts"
- "Show me subscription changes in the last 3 months"

### Data Visualization Requests
- "Create a chart showing invoice volumes by month"
- "Show me a pie chart of customers by segment"
- "Create a line chart showing MRR growth over time"

## Sample Output Formats

### Single Result
```
We have 204 customers.
```

### Multiple Results (Markdown Table)
```markdown
| Year | Count |
|------|-------|
| 2022 | 170   |
| 2023 | 201   |
| 2024 | 229   |
| 2025 | 38    |
```

## Architecture

### Core Components

```
neo4j_database_agent/
├── __init__.py           # Package exports
├── agent.py              # Main agent implementation
├── agent_factory.py      # Agent factory for deployment
└── tools.py              # Neo4j tools and functions

eval/
├── data/                 # Evaluation test cases
├── baseline_results.json # Performance baselines
├── eval.md              # Evaluation guide
└── generate_baseline.py # Baseline generation

app.py                   # Flask web UI for deployment management
install.sh              # Installation and setup script
start.sh                # Application startup script
```

### Agent Tools (4 Core Tools)

1. **`check_schema_cache`** - Fast schema availability check
2. **`get_neo4j_schema`** - Database schema discovery and caching
3. **`execute_cypher_query`** - Query execution with table formatting
4. **`refresh_neo4j_schema`** - Schema cache refresh

### Performance Features

- **Schema Caching**: First query caches schema, subsequent queries use cache
- **Connection Pooling**: Efficient Neo4j connection management with timeouts
- **Query Optimization**: Automatic LIMIT and ORDER BY suggestions
- **Smart Formatting**: Markdown tables for clear data presentation

## Model Evaluation

The project includes a comprehensive evaluation system:

```bash
# Generate performance baseline
cd eval
python generate_baseline.py

# Compare different models
export MODEL_NAME=gemini-2.5-pro
python generate_baseline.py --output pro_baseline.json

# Run ADK evaluation
adk eval neo4j_database_agent data/baseline_queries.test.json
```

See `eval/eval.md` for detailed evaluation instructions.

## Security

### Read-Only Operations
- Only MATCH, RETURN, WITH, WHERE, ORDER BY, LIMIT operations allowed
- All write operations (CREATE, MERGE, SET, DELETE) are blocked
- Procedure calls are validated for safety

### Query Safety Features
- **Intent Analysis**: Detects destructive patterns in natural language
- **Cypher Validation**: Deep analysis of generated queries
- **Connection Timeouts**: 10-second timeout prevents hanging

### Best Practices
- Store credentials securely in `.env` (never commit this file)
- Use Neo4j read-only users for additional security
- Monitor query patterns and performance

## Environment Variable Priority

⚠️ **Important**: The agent uses `load_dotenv(override=True)` to ensure `.env` files take precedence over shell environment variables. This means your `.env` configuration will always be used, regardless of shell variables.

## Troubleshooting

### Connection Errors
**Problem**: Cannot connect to Neo4j
**Solution**: 
- Verify NEO4J_URI format (use neo4j+s:// for secure connections)
- Check firewall rules and network access
- Confirm credentials and database availability

### Performance Issues
**Problem**: Slow response times
**Solution**: Schema caching should resolve after first query. Use `refresh_neo4j_schema` if needed

### Model Configuration
**Problem**: Wrong model being used
**Solution**: Check `.env` file for `MODEL_NAME` setting - this overrides any shell variables

## Development

### Testing Changes
1. Test locally with `adk web`
2. Run evaluation: `cd eval && python generate_baseline.py`
3. Deploy and test: `./start.sh`

### Adding New Query Types
1. Update agent instructions in `neo4j_database_agent/agent.py`
2. Add new tools in `neo4j_database_agent/tools.py` if needed
3. Test with the evaluation system

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly with local and deployed agent
5. Run evaluation to ensure performance
6. Submit a pull request

## License

This project is licensed under the Apache License 2.0.

---

**Built with Google Agent Development Kit (ADK) and Neo4j**