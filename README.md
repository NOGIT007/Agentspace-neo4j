# Agentspace Neo4j Agent

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
- 📅 **Time-based Queries**: "show orders from last month", "products created today"
- 📈 **Aggregations**: Count, sum, average with GROUP BY and ORDER BY
- 💰 **Financial Calculations**: Revenue totals, MRR analysis with grand totals
- 🔗 **Relationship Analysis**: Customer orders, product categories, connections
- 📋 **Table Formatting**: Automatic table formatting for multi-row results

### Security Features
- 🛡️ **Query Intent Analysis**: Fast detection of destructive operations
- 🚫 **Write Operation Blocking**: Prevents CREATE, UPDATE, DELETE operations
- 💡 **Helpful Suggestions**: Reformulation guidance for blocked queries
- ⚡ **< 50ms Security Check**: Fast security validation without performance impact

## Prerequisites

- Python 3.11 or higher
- Google Cloud Project with Vertex AI enabled
- Neo4j database (AuraDB or self-hosted)
- `uv` package manager installed

## Installation

1. Clone the repository:
```bash
git clone https://github.com/your-username/Agentspace-neo4j.git
cd Agentspace-neo4j
```

2. Run the installation script:
```bash
./install.sh
```

3. Configure your environment variables by creating a `.env` file:
```bash
# Google Cloud Configuration
GOOGLE_GENAI_USE_VERTEXAI=True
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_CLOUD_LOCATION=europe-west1
GOOGLE_API_KEY=your-api-key
GOOGLE_CLOUD_STORAGE=gs://your-storage-bucket
MODEL_NAME=gemini-2.5-flash

# Neo4j Configuration
NEO4J_URI=neo4j+s://your-instance.endpoints.neo4j.io
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your-password
NEO4J_DATABASE=neo4j
NEO4J_CONNECTION_TIMEOUT=30
NEO4J_MAX_CONNECTION_LIFETIME=3600

# Agent Configuration
APP_ID=your-app-id
```

## Usage

### Local Development & Testing

1. Activate the virtual environment:
```bash
source .venv/bin/activate
```

2. Start the ADK web interface:
```bash
adk web
```

3. Open your browser and navigate to the provided URL (typically http://localhost:8080)

### Example Queries

The agent supports a wide range of natural language queries:

#### Basic Queries
- "List all my customers"
- "Show me all products" 
- "Count orders in the database"

#### Time-based Analysis
- "Show orders from last week"
- "Products created today"
- "Revenue from last month"

#### Financial & Business Analytics
- "List subscription MRR order by customer with grand total"
- "Top 10 customers by revenue"
- "Monthly revenue totals"
- "Customer lifetime value analysis"

#### Aggregations & Reporting
- "Count customers by city"
- "Average order value by product category"
- "Total sales by region"

### How It Works

1. **Security Check**: Query intent is analyzed for destructive operations (< 50ms)
2. **Schema Discovery**: Database schema is retrieved and cached for performance
3. **Query Generation**: Natural language is converted to optimized Cypher queries
4. **Execution**: Safe, read-only queries are executed against Neo4j
5. **Formatting**: Results are presented in business-friendly tables with totals

## Architecture

### Core Components

```
agents/
├── agent.py          # Main agent with enhanced instructions and tools
├── security.py       # Security callback and query intent analysis  
└── query_utils.py    # Utility functions for common query patterns

app.py               # Flask web UI for deployment management
install.sh           # Installation and setup script
start.sh            # Application startup script
```

### Security Architecture

- **Pre-LLM Security**: Callback intercepts queries before model processing
- **Pattern Detection**: Regex-based analysis of destructive intent
- **Contextual Analysis**: Distinguishes "update me" vs "update database"
- **Query Validation**: Deep Cypher analysis for write operation detection

### Performance Features

- **Schema Caching**: First query caches schema, subsequent queries use cache
- **Connection Pooling**: Efficient Neo4j connection management
- **Query Optimization**: Automatic LIMIT and ORDER BY suggestions

## Deployment to Vertex AI

### Web UI Deployment

1. Start the Flask application:
```bash
./start.sh
```

2. Navigate to http://localhost:5000

3. Use the web interface to:
   - Deploy agent to Vertex AI Agent Engine
   - Test deployed agent
   - Register to Agentspace
   - Manage deployed agents

### Manual Deployment

```bash
# Deploy using ADK CLI
adk deploy --project YOUR_PROJECT_ID --location europe-west1

# Or test locally first
python test_agent_local.py
```

## Security

### Read-Only Operations
- Only MATCH, RETURN, WITH, WHERE, ORDER BY, LIMIT operations allowed
- All write operations (CREATE, MERGE, SET, DELETE) are blocked
- Procedure calls are validated for safety

### Query Safety Features
- **Intent Analysis**: Detects destructive patterns in natural language
- **Cypher Validation**: Deep analysis of generated queries
- **Helpful Errors**: Provides reformulation suggestions for blocked queries

### Best Practices
- Store credentials securely in `.env` (never commit this file)
- Use Neo4j read-only users for additional security
- Monitor query patterns and performance

## Advanced Features

### Grand Total Calculations
The agent automatically includes grand totals when requested:
```
Query: "List subscription MRR by customer with grand total"
Result: Individual customer MRR + calculated grand total
```

### Table Formatting
Multi-row results are automatically formatted as business-friendly tables with:
- Clear column headers
- Proper data alignment
- Grand totals when applicable

### Query Utility Functions
- `build_time_filter()`: Generate time-based WHERE clauses
- `build_aggregation_query()`: Create GROUP BY queries
- `build_grand_total_query()`: Queries with individual values and totals

## Troubleshooting

### Security Issues
**Problem**: Legitimate query blocked by security
**Solution**: Rephrase using "show me", "list", or "find" instead of action verbs

### Performance Issues
**Problem**: Slow response times
**Solution**: Schema caching should resolve after first query. Use `refresh_neo4j_schema` if needed

### Connection Errors
**Problem**: Cannot connect to Neo4j
**Solution**: 
- Verify NEO4J_URI format (use neo4j+s:// for secure connections)
- Check firewall rules and network access
- Confirm credentials and database availability

## Development

### Adding New Query Types

1. Update agent instructions in `agents/agent.py`
2. Add utility functions in `agents/query_utils.py` if needed
3. Test with `adk web`

### Security Enhancements

1. Modify patterns in `agents/security.py`
2. Test with various query types
3. Ensure < 50ms performance requirement

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly with `adk web`
5. Submit a pull request

## License

This project is proprietary software. All rights reserved.

## Support

For issues and questions:
- Create an issue in the repository
- Contact the development team

---

**Built with Google Agent Development Kit (ADK) and Neo4j**