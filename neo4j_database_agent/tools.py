"""
Neo4j Database Agent Tools

This module provides tools for interacting with Neo4j databases,
following Google ADK patterns for simplicity and reliability.
"""

import os
import json
import logging
from datetime import date, datetime
from neo4j import GraphDatabase
from dotenv import load_dotenv
from .simple_charts import format_as_chart

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global cache for schema (simple in-memory cache)
_schema_cache = {}

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
        logger.error(f"Neo4j query failed: {e}")
        return json.dumps({"error": str(e)})

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
        logger.warning("Query complexity limit exceeded")
        return False
    
    return True

def _format_results_as_table(results: list) -> str:
    """
    Format query results as a clean markdown table.
    """
    if not results:
        return "No results found."
    
    # Get all keys from first result
    if not results[0]:
        return "No results found."
    
    keys = list(results[0].keys())
    
    # Single result - format as key-value pairs
    if len(results) == 1:
        output = []
        for key, value in results[0].items():
            output.append(f"**{key}**: {value}")
        return "\n".join(output)
    
    # Multiple results - format as markdown table
    output = []
    
    # Calculate column widths for proper alignment
    col_widths = {}
    for key in keys:
        col_widths[key] = max(len(str(key)), max(len(str(result.get(key, ''))) for result in results))
        col_widths[key] = min(col_widths[key], 20)  # Cap at 20 chars
    
    # Create markdown table header
    header_row = "| " + " | ".join(f"{key:<{col_widths[key]}}" for key in keys) + " |"
    separator_row = "|" + "|".join(f":{'-' * col_widths[key]}:" for key in keys) + "|"
    
    output.append(header_row)
    output.append(separator_row)
    
    # Add data rows
    for result in results:
        row_values = []
        for key in keys:
            value = str(result.get(key, ''))
            if len(value) > col_widths[key]:
                value = value[:col_widths[key]-3] + "..."
            row_values.append(f"{value:<{col_widths[key]}}")
        
        row = "| " + " | ".join(row_values) + " |"
        output.append(row)
    
    # Add summary for multiple rows
    if len(results) > 1:
        
        # Check if there are numeric columns for totals
        numeric_totals = {}
        for key in keys:
            try:
                total = sum(float(result.get(key, 0)) for result in results if isinstance(result.get(key), (int, float)))
                if total > 0:
                    numeric_totals[key] = total
            except:
                pass
        
        if numeric_totals:
            output.append("")
            output.append("**Summary:**")
            for key, total in numeric_totals.items():
                formatted_total = f"{total:,.0f}" if total == int(total) else f"{total:,.2f}"
                output.append(f"- Total {key}: {formatted_total}")
        
        output.append("")
        output.append(f"*Total rows: {len(results)}*")
    
    return "\n".join(output)

# Tool functions
def check_schema_cache() -> str:
    """
    Checks if the schema is already cached in memory.
    Call this FIRST before get_neo4j_schema to avoid redundant database queries.
    
    Returns:
        JSON with cache status and schema if cached.
    """
    if "schema" in _schema_cache:
        logger.info("Schema found in cache")
        return json.dumps({
            "cached": True,
            "schema": _schema_cache["schema"],
            "message": "Schema is cached. Use the provided schema directly without calling get_neo4j_schema."
        }, indent=2)
    else:
        logger.info("No schema in cache")
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
    """
    logger.info("Executing tool: get_neo4j_schema")
    
    # Check if schema is already cached
    if "schema" in _schema_cache:
        logger.info("Returning cached schema from memory")
        cached_schema = _schema_cache["schema"].copy()
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
    logger.info("Schema cached in memory")
    
    # Add instruction for the agent
    schema_info["_instruction"] = "Schema retrieved from database. Now use execute_cypher_query to query the data based on the user's request."
    schema_info["_cached"] = False
    
    return json.dumps(schema_info, indent=2)

def execute_cypher_query(cypher_query: str) -> str:
    """
    Executes a read-only Cypher query against the Neo4j database.

    Use this tool after understanding the database schema from get_neo4j_schema.

    Args:
        cypher_query: The Cypher query to execute (read-only operations only)

    Returns:
        Formatted table string with query results or error information

    Security:
        Only allows read operations (MATCH, RETURN). Write operations
        (CREATE, MERGE, SET, DELETE) are blocked for safety.
    """
    logger.info(f"Executing tool: execute_cypher_query with query='{cypher_query}'")

    # Enhanced security check: Deep validation of Cypher queries
    if not _validate_query_safety(cypher_query):
        return json.dumps({
            "error": "Only read-only queries are allowed. Write operations are blocked for safety.",
            "suggestion": "Use MATCH and RETURN statements for querying data."
        })

    # Execute query and get JSON results
    json_results = _execute_query(cypher_query)
    
    try:
        # Parse JSON results
        results = json.loads(json_results)
        
        # Check for errors
        if isinstance(results, dict) and "error" in results:
            return json_results
        
        # Format as table for better readability
        if isinstance(results, list) and results:
            formatted_table = _format_results_as_table(results)
            return f"Query Results:\n{formatted_table}"
        else:
            return "No results found."
            
    except json.JSONDecodeError:
        return json_results  # Return original if can't parse

def refresh_neo4j_schema() -> str:
    """
    Clears the cached schema and forces a fresh retrieval on the next schema request.
    
    Use this tool when you need to refresh the schema after database structure changes.
    
    Returns:
        Success message indicating the schema cache has been cleared.
    """
    logger.info("Executing tool: refresh_neo4j_schema")
    
    # Clear the cached schema
    if "schema" in _schema_cache:
        del _schema_cache["schema"]
        logger.info("Schema cache cleared")
        return json.dumps({"status": "success", "message": "Schema cache has been cleared. Next schema request will fetch fresh data from Neo4j."})
    else:
        return json.dumps({"status": "info", "message": "No cached schema found."})

def create_simple_chart(cypher_query: str) -> str:
    """
    Create a simple ASCII bar chart from query results.
    
    Use this tool when users ask for charts, graphs, or visualizations.
    Works best with aggregated data that has labels and numeric values.
    
    Args:
        cypher_query: The Cypher query to execute and visualize
        
    Returns:
        ASCII bar chart visualization of the data
    """
    logger.info(f"Executing tool: create_simple_chart with query='{cypher_query}'")
    
    # Enhanced security check
    if not _validate_query_safety(cypher_query):
        return json.dumps({
            "error": "Only read-only queries are allowed for charts.",
            "suggestion": "Use MATCH and RETURN statements for querying data."
        })
    
    # Execute query and get raw JSON results
    json_results = _execute_query(cypher_query)
    
    try:
        # Parse JSON results
        results = json.loads(json_results)
        
        # Check for errors
        if isinstance(results, dict) and "error" in results:
            return json_results
        
        # Create chart from results
        if isinstance(results, list) and results:
            chart = format_as_chart(json_results)
            return chart
        else:
            return "No data to visualize"
            
    except json.JSONDecodeError:
        return json_results  # Return original if can't parse

def execute_advanced_aggregation(cypher_query: str) -> str:
    """
    Execute advanced aggregation queries with enhanced formatting for totals, subtotals, and comparisons.
    
    Use this tool for complex queries involving:
    - Grand totals and subtotals
    - Time period comparisons
    - Multiple aggregations (count, sum, avg, etc.)
    - Percentage calculations
    - Running totals
    
    Args:
        cypher_query: The Cypher query to execute
        
    Returns:
        Formatted results with enhanced summaries and totals
    """
    logger.info(f"Executing tool: execute_advanced_aggregation with query='{cypher_query}'")
    
    # Enhanced security check
    if not _validate_query_safety(cypher_query):
        return json.dumps({
            "error": "Only read-only queries are allowed.",
            "suggestion": "Use MATCH and RETURN statements for querying data."
        })
    
    # Execute query and get raw JSON results
    json_results = _execute_query(cypher_query)
    
    try:
        # Parse JSON results
        results = json.loads(json_results)
        
        # Check for errors
        if isinstance(results, dict) and "error" in results:
            return json_results
        
        # Format with enhanced aggregation support
        if isinstance(results, list) and results:
            formatted_table = _format_results_as_table(results)
            return f"Query Results:\n{formatted_table}"
        else:
            return "No results found."
            
    except json.JSONDecodeError:
        return json_results  # Return original if can't parse