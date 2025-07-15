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
- 📊 **Chart Visualizations**: ASCII bar charts for data visualization
- 🧧 **Invoice Analytics**: Robust invoice counting with correct property handling

### Advanced Analytics
- 📊 **Grand Totals & Subtotals**: Automatic totals for all numeric columns
- 📈 **Year-over-Year Analysis**: Compare data across time periods
- 🎯 **Top N Queries**: Find top customers, products, categories
- 📊 **Percentage Calculations**: Breakdown by category with percentages
- 🏃 **Running Totals**: Cumulative calculations over time
- 📋 **Multiple Aggregations**: Count, sum, average in single query

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

### Direct Deployment

```bash
# Deploy using the deployment script
uv run python deployment/deploy.py

# Or test locally first
uv run python -c "from neo4j_database_agent import root_agent; print(root_agent.name)"
```

## Example Queries

The agent supports a wide range of natural language queries with enhanced formatting:

### Basic Queries
- "List all my customers"
- "Show me all products" 
- "Count orders in the database"

### Time-based Analysis
- "Show invoices by year" → Returns markdown table with totals
- "Compare quarterly revenue" → Year/quarter breakdown
- "Monthly sales from last year" → Time period filtering

### Financial & Business Analytics
- "Revenue by customer with totals" → Subtotals and grand totals
- "Top 10 customers by revenue" → Ranked results
- "Invoice count by year" → Properly uses `issue_date` property
- "Show me a chart of invoices per year" → ASCII bar chart

### Advanced Aggregations
- "Count customers by city with percentages" → Percentage calculations
- "Running total of monthly sales" → Cumulative calculations
- "Average order value by product category" → Multiple aggregations

### Chart Visualizations
- "Create a bar chart of sales by year"
- "Show me a graph of customer counts by region"
- "Visualize invoice distribution by month"

## Sample Output Formats

### Single Result
```
**total_invoices**: 641
```

### Multiple Results (Markdown Table)
```markdown
| year | count |
|:----:|:-----:|
| 2022 | 170   |
| 2023 | 201   |
| 2024 | 229   |
| 2025 | 38    |

**Summary:**
- Total count: 638
*Total rows: 4*
```

### Chart Visualization
```
Data Visualization
==================
2022 : █████████████████████████████            170
2023 : ███████████████████████████████████      201
2024 : ████████████████████████████████████████ 229
2025 : ██████                                   38
Total: 638
```

## Architecture

### Core Components

```
neo4j_database_agent/
├── __init__.py           # Package exports
├── agent.py              # Main agent with enhanced instructions and 6 tools
├── tools.py              # Core tools for querying and visualization
└── simple_charts.py      # ASCII chart generation

deployment/
├── deploy.py             # Vertex AI deployment script
└── test_deployment.py    # Deployment testing

app.py                    # Flask web UI for deployment management
install.sh               # Installation and setup script
start.sh                 # Application startup script
```

### Agent Tools (6 Total)

1. **`check_schema_cache`** - Fast schema availability check
2. **`get_neo4j_schema`** - Database schema discovery and caching
3. **`execute_cypher_query`** - Standard query execution with table formatting
4. **`execute_advanced_aggregation`** - Enhanced aggregation with automatic totals
5. **`create_simple_chart`** - ASCII bar chart generation
6. **`refresh_neo4j_schema`** - Schema cache refresh

### Security Architecture

- **Pre-LLM Security**: Callback intercepts queries before model processing
- **Pattern Detection**: Regex-based analysis of destructive intent
- **Contextual Analysis**: Distinguishes "update me" vs "update database"
- **Query Validation**: Deep Cypher analysis for write operation detection

### Performance Features

- **Schema Caching**: First query caches schema, subsequent queries use cache
- **Connection Pooling**: Efficient Neo4j connection management
- **Query Optimization**: Automatic LIMIT and ORDER BY suggestions
- **Smart Formatting**: Single results vs multi-row table detection

## Query Patterns Supported

### Count & Aggregation
- Simple counts: `MATCH (n:Node) RETURN count(n) as total`
- Group counts: `MATCH (n:Node) RETURN n.category, count(n) as count`
- Multiple aggregations: `count()`, `sum()`, `avg()`, `min()`, `max()`
- Conditional counts with `WHERE` clauses

### Totals & Subtotals
- Grand totals: `MATCH (n:Node) RETURN sum(n.amount) as grand_total`
- Subtotals by group: `MATCH (n:Node) RETURN n.category, sum(n.amount) as subtotal`
- Multiple totals: count, sum, average in one query
- **Automatic totals** for all numeric columns

### Time & Date Comparisons
- Year comparison: `date(n.date).year`
- Month comparison: `date(n.date).month`
- Quarter comparison: `(date(n.date).month-1)/3+1`
- Date ranges: `WHERE n.date >= date('2023-01-01')`
- Year-over-year changes with `lag()` functions

### Advanced Patterns
- Percentages: `round(100.0 * count(n) / total, 2)`
- Running totals: `sum(count(n)) OVER (ORDER BY year)`
- Top N queries: `ORDER BY count DESC LIMIT 10`

## Critical Invoice Property

⚠️ **Important**: For Invoice nodes, the agent correctly uses `issue_date` property (underscore) not `issueDate` (camelCase):
- ✅ **Correct**: `i.issue_date` - contains complete invoice data (638 invoices)
- ❌ **Wrong**: `i.issueDate` - contains only partial data (3 invoices)

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

1. Update agent instructions in `neo4j_database_agent/agent.py`
2. Add new tools in `neo4j_database_agent/tools.py` if needed
3. Test with the web UI

### Security Enhancements

1. Modify patterns in query validation
2. Test with various query types
3. Ensure < 50ms performance requirement

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly with local and deployed agent
5. Submit a pull request

## License

This project is proprietary software. All rights reserved.

## Support

For issues and questions:
- Create an issue in the repository
- Contact the development team

---

**Built with Google Agent Development Kit (ADK) and Neo4j**