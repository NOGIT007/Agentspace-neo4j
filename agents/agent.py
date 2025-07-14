import os
import json
import logging
from datetime import date, datetime
from neo4j import GraphDatabase
from google.adk.agents import LlmAgent
from dotenv import load_dotenv
from .security import query_security_callback

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)

def _make_serializable(obj):
    """
    Helper function that recursively finds non-serializable objects (like dates)
    and converts them to strings for JSON serialization.
    """
    if isinstance(obj, dict):
        return {k: _make_serializable(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_make_serializable(i) for i in obj]
    # Check for Neo4j and standard Python date/datetime objects
    if isinstance(obj, (date, datetime)) or (hasattr(obj, '__module__') and obj.__module__.startswith('neo4j.time')):
        return str(obj)
    return obj

def _execute_query(query: str, params: dict = None) -> str:
    """
    Private helper function to execute a Cypher query safely.
    Creates a new database connection for each query.
    """
    if params is None:
        params = {}
    
    try:
        # Create a new driver connection for each query
        with GraphDatabase.driver(
            os.getenv("NEO4J_URI", "bolt://localhost:7687"),
            auth=(
                os.getenv("NEO4J_USERNAME", "neo4j"), 
                os.getenv("NEO4J_PASSWORD", "password")
            ),
            database=os.getenv("NEO4J_DATABASE", "neo4j")
        ) as driver:
            with driver.session() as session:
                result = session.run(query, params)
                records = [record.data() for record in result]
                # Convert records to be JSON-serializable
                serializable_records = _make_serializable(records)
                return json.dumps(serializable_records, indent=2)
    except Exception as e:
        logging.error(f"Neo4j query failed: {e}")
        return json.dumps({"error": str(e)})

# Global cache for schema (simple in-memory cache)
_schema_cache = {}

# Define tools following ADK guidelines
def check_schema_cache() -> str:
    """
    Checks if the schema is already cached in memory.
    Call this FIRST before get_neo4j_schema to avoid redundant database queries.
    
    Returns:
        JSON with cache status and schema if cached.
    """
    if "schema" in _schema_cache:
        logging.info("Schema found in cache")
        return json.dumps({
            "cached": True,
            "schema": _schema_cache["schema"],
            "message": "Schema is cached. Use the provided schema directly without calling get_neo4j_schema."
        }, indent=2)
    else:
        logging.info("No schema in cache")
        return json.dumps({
            "cached": False,
            "message": "No schema cached. You need to call get_neo4j_schema first."
        })

def get_neo4j_schema() -> str:
    """
    Retrieves the database schema from Neo4j.
    Only call this if check_schema_cache indicates no cached schema exists.

    Returns:
        JSON string containing nodes, relationships, and their properties.
        IMPORTANT: After receiving this schema, you MUST continue to create
        and execute a Cypher query using execute_cypher_query.
    """
    logging.info("Executing tool: get_neo4j_schema")
    
    # Check if schema is already cached
    if "schema" in _schema_cache:
        logging.info("Returning cached schema from memory")
        cached_schema = _schema_cache["schema"].copy()
        # Add instruction for the agent
        cached_schema["_instruction"] = "Schema retrieved from cache. Now use execute_cypher_query to query the data based on the user's request."
        cached_schema["_cached"] = True
        return json.dumps(cached_schema, indent=2)
    
    # Get all node labels
    labels_query = "CALL db.labels() YIELD label RETURN collect(label) as labels"
    
    # Get all relationship types
    rels_query = "CALL db.relationshipTypes() YIELD relationshipType RETURN collect(relationshipType) as relationships"
    
    labels_result = json.loads(_execute_query(labels_query))
    rels_result = json.loads(_execute_query(rels_query))
    
    # Get sample nodes for each label to understand properties
    schema_info = {
        "labels": labels_result[0]["labels"] if labels_result else [],
        "relationships": rels_result[0]["relationships"] if rels_result else [],
        "node_properties": {}
    }
    
    # For each label, get sample properties
    for label in schema_info["labels"]:
        sample_query = f"MATCH (n:{label}) RETURN n LIMIT 1"
        sample_result = json.loads(_execute_query(sample_query))
        if sample_result:
            schema_info["node_properties"][label] = list(sample_result[0]["n"].keys())
    
    # Save schema to cache for future use
    _schema_cache["schema"] = schema_info.copy()
    logging.info("Schema cached in memory")
    
    # Add instruction for the agent
    schema_info["_instruction"] = "Schema retrieved from database. Now use execute_cypher_query to query the data based on the user's request."
    schema_info["_cached"] = False
    
    return json.dumps(schema_info, indent=2)

def refresh_neo4j_schema() -> str:
    """
    Clears the cached schema and forces a fresh retrieval on the next schema request.
    
    Use this tool when you need to refresh the schema after database structure changes.
    
    Returns:
        Success message indicating the schema cache has been cleared.
    """
    logging.info("Executing tool: refresh_neo4j_schema")
    
    # Clear the cached schema
    if "schema" in _schema_cache:
        del _schema_cache["schema"]
        logging.info("Schema cache cleared")
        return json.dumps({"status": "success", "message": "Schema cache has been cleared. Next schema request will fetch fresh data from Neo4j."})
    else:
        return json.dumps({"status": "info", "message": "No cached schema found."})

def execute_cypher_query(cypher_query: str) -> str:
    """
    Executes a read-only Cypher query against the Neo4j database.

    Use this tool after understanding the database schema from get_neo4j_schema.

    Args:
        cypher_query: The Cypher query to execute (read-only operations only)

    Returns:
        JSON string with query results or error information

    Security:
        Only allows read operations (MATCH, RETURN). Write operations
        (CREATE, MERGE, SET, DELETE) are blocked for safety.
    """
    logging.info(f"Executing tool: execute_cypher_query with query='{cypher_query}'")

    # Enhanced security check: Deep validation of Cypher queries
    if not _validate_query_safety(cypher_query):
        return json.dumps({
            "error": "Only read-only queries are allowed. Write operations are blocked for safety.",
            "suggestion": "Use MATCH and RETURN statements for querying data."
        })

    return _execute_query(cypher_query)

def _validate_query_safety(cypher_query: str) -> bool:
    """
    Enhanced validation to ensure query is safe for execution.
    
    Args:
        cypher_query: The Cypher query to validate
        
    Returns:
        True if query is safe, False if potentially dangerous
    """
    if not cypher_query:
        return False
    
    query_upper = cypher_query.upper().strip()
    
    # Direct write operation keywords
    write_keywords = [
        "CREATE", "MERGE", "SET", "DELETE", "REMOVE", "DROP", 
        "DETACH DELETE", "FOREACH", "LOAD CSV"
    ]
    
    # Check for explicit write operations
    for keyword in write_keywords:
        if keyword in query_upper:
            return False
    
    # Check for procedure calls that might modify data
    if "CALL" in query_upper:
        dangerous_procedures = [
            "apoc.create", "apoc.merge", "apoc.refactor", "apoc.periodic.commit",
            "db.create", "db.drop", "dbms.security"
        ]
        query_lower = cypher_query.lower()
        if any(proc in query_lower for proc in dangerous_procedures):
            return False
    
    # Basic complexity limits (prevent resource exhaustion)
    if query_upper.count("MATCH") > 10:  # Arbitrary limit for complex joins
        logging.warning("Query complexity limit exceeded")
        return False
    
    return True

# Create the agent following ADK guidelines
root_agent = LlmAgent(
    model=os.getenv("MODEL_NAME", "gemini-2.5-flash"),
    name="neo4j_database_agent",
    description="An intelligent agent that queries Neo4j databases using natural language",
    output_key="neo4j_schema_state",  # This will save the schema to session state
    before_model_callback=query_security_callback,  # Security callback for query validation
    instruction=(
        "You are an expert Neo4j database assistant. Your job is to help users query their Neo4j database.\n\n"
        
        "CRITICAL WORKFLOW - YOU MUST FOLLOW THIS EXACTLY:\n"
        "1. ALWAYS start by calling check_schema_cache to see if schema is already available\n"
        "2. If cache check returns cached=true, use the provided schema directly (DO NOT call get_neo4j_schema)\n"
        "3. If cache check returns cached=false, then call get_neo4j_schema\n"
        "4. Analyze the schema to find relevant nodes and properties\n"
        "5. Call execute_cypher_query with an appropriate Cypher query\n"
        "6. Present the results in a clear, formatted response\n\n"
        
        "IMPORTANT CACHING RULES:\n"
        "- ALWAYS call check_schema_cache first for EVERY query\n"
        "- NEVER call get_neo4j_schema if check_schema_cache returns the schema\n"
        "- This saves time by avoiding redundant database queries\n\n"
        
        "IMPORTANT: This is a MULTI-STEP process. After getting the schema, you MUST continue "
        "to create and execute a Cypher query. Do not stop after just getting the schema!\n\n"
        
        "Example workflow:\n"
        "First query: 'list all my customers'\n"
        "- Step 1: Call check_schema_cache → returns cached=false\n"
        "- Step 2: Call get_neo4j_schema → retrieves and caches schema\n"
        "- Step 3: Find Customer nodes in schema\n"
        "- Step 4: Call execute_cypher_query with: MATCH (c:Customer) RETURN c\n"
        "- Step 5: Present the customer data\n\n"
        
        "Second query: 'show me all products'\n"
        "- Step 1: Call check_schema_cache → returns cached=true WITH the schema\n"
        "- Step 2: Use the schema from cache check (DO NOT call get_neo4j_schema)\n"
        "- Step 3: Find Product nodes in the cached schema\n"
        "- Step 4: Call execute_cypher_query with: MATCH (p:Product) RETURN p\n"
        "- Step 5: Present the product data\n\n"
        
        "CYPHER QUERY EXAMPLES:\n"
        "\n"
        "Basic Queries:\n"
        "- List all customers: MATCH (c:Customer) RETURN c\n"
        "- Get customer by name: MATCH (c:Customer {name: 'John'}) RETURN c\n"
        "- Count nodes: MATCH (n:Customer) RETURN count(n) as count\n"
        "- Get with limit: MATCH (c:Customer) RETURN c LIMIT 10\n\n"
        
        "Time/Date Queries:\n"
        "- Orders from last week: MATCH (o:Order) WHERE o.date >= date() - duration('P7D') RETURN o\n"
        "- Products created today: MATCH (p:Product) WHERE date(p.created) = date() RETURN p\n"
        "- Records from specific month: MATCH (n) WHERE date.truncate('month', n.timestamp) = date('2024-01') RETURN n\n"
        "- Events in date range: MATCH (e:Event) WHERE e.date >= date('2024-01-01') AND e.date <= date('2024-12-31') RETURN e\n\n"
        
        "Aggregation & Ordering:\n"
        "- Count customers by city: MATCH (c:Customer) RETURN c.city, count(c) as customer_count ORDER BY customer_count DESC\n"
        "- Top 10 products by sales: MATCH (p:Product) RETURN p ORDER BY p.sales DESC LIMIT 10\n"
        "- Average price by category: MATCH (p:Product) RETURN p.category, avg(p.price) as avg_price ORDER BY avg_price DESC\n"
        "- Group orders by status: MATCH (o:Order) RETURN o.status, count(o) as order_count ORDER BY order_count DESC\n\n"
        
        "Calculations:\n"
        "- Total revenue by month: MATCH (o:Order) RETURN date.truncate('month', o.date) as month, sum(o.amount) as total_revenue ORDER BY month\n"
        "- Subtotal by category: MATCH (p:Product) RETURN p.category, sum(p.price) as subtotal ORDER BY subtotal DESC\n"
        "- Customer lifetime value: MATCH (c:Customer)-[:PLACED]->(o:Order) RETURN c.name, sum(o.total) as lifetime_value ORDER BY lifetime_value DESC\n"
        "- Monthly growth: MATCH (o:Order) WITH date.truncate('month', o.date) as month, sum(o.amount) as monthly_total RETURN month, monthly_total, monthly_total - lag(monthly_total) OVER (ORDER BY month) as growth\n"
        "- Grand totals: Use WITH clause to calculate both details and grand total in same query\n\n"
        
        "Advanced Query Patterns:\n"
        "- Details with Grand Total: MATCH (c:Customer) WITH c, c.mrr as individual_mrr, sum(c.mrr) OVER () as grand_total RETURN c.name, individual_mrr, grand_total ORDER BY individual_mrr DESC\n"
        "- Multiple aggregation levels: MATCH (o:Order) RETURN o.category, count(o) as count, sum(o.amount) as subtotal WITH collect({category: o.category, count: count, subtotal: subtotal}) as details, sum(subtotal) as grand_total RETURN details, grand_total\n\n"
        
        "Relationship Queries:\n"
        "- Customer orders: MATCH (c:Customer)-[:PLACED]->(o:Order) RETURN c.name, collect(o) as orders\n"
        "- Product categories: MATCH (p:Product)-[:BELONGS_TO]->(cat:Category) RETURN cat.name, count(p) as product_count\n"
        "- Connected nodes: MATCH (n)-[r]-(m) RETURN n, type(r), m LIMIT 20\n\n"
        
        "ALWAYS:\n"
        "- Complete ALL steps, don't stop after schema retrieval\n"
        "- Use the exact node labels and property names from the schema\n"
        "- Only use read operations (MATCH, RETURN, WITH, WHERE, ORDER BY, LIMIT)\n"
        "- Present actual data, not just descriptions\n"
        "- Use appropriate date functions for time-based queries\n"
        "- Include ORDER BY and LIMIT for large result sets\n"
        "- Use aggregation functions (count, sum, avg, max, min) for calculations\n\n"
        
        "RESULT FORMATTING RULES:\n"
        "- For 2+ rows of data: Format as a proper table with headers\n"
        "- For queries requesting 'grand total' or 'total': Include both individual values AND the calculated grand total\n"
        "- Use OVER() window functions or WITH clauses to calculate grand totals alongside details\n"
        "- When showing financial data (MRR, revenue, etc.): Always include totals when requested\n"
        "- Present results in clear, business-friendly format with appropriate column headers\n\n"
        
        "SCHEMA CACHING:\n"
        "- The schema is automatically cached after the first retrieval for better performance\n"
        "- Use refresh_neo4j_schema if you need to clear the cache and fetch fresh schema\n\n"
        
        "SECURITY:\n"
        "- Only read-only operations are allowed for data safety\n"
        "- Write operations (CREATE, UPDATE, DELETE) are automatically blocked\n"
        "- Focus on querying, analyzing, and reporting data\n\n"
        
        "Remember: Getting the schema is just step 1. You MUST continue to query the data!"
    ),
    tools=[check_schema_cache, get_neo4j_schema, execute_cypher_query, refresh_neo4j_schema]  # Pass functions directly as tools
)