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

# Load environment variables (override existing shell vars)
load_dotenv(override=True)

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
    Creates a new database connection for each query with timeout.
    """
    if params is None:
        params = {}
    
    try:
        # Create a new driver connection for each query with timeout
        with GraphDatabase.driver(
            os.getenv("NEO4J_URI", "bolt://localhost:7687"),
            auth=(
                os.getenv("NEO4J_USERNAME", "neo4j"), 
                os.getenv("NEO4J_PASSWORD", "password")
            ),
            database=os.getenv("NEO4J_DATABASE", "neo4j"),
            connection_timeout=10,  # 10 second timeout
            max_connection_lifetime=30  # 30 second max connection lifetime
        ) as driver:
            with driver.session() as session:
                result = session.run(query, params)
                records = [record.data() for record in result]
                # Convert records to be JSON-serializable
                serializable_records = _make_serializable(records)
                return json.dumps(serializable_records, indent=2)
    except Exception as e:
        logger.error(f"Neo4j query failed: {e}")
        return json.dumps({"error": f"Database connection failed: {str(e)}. Please check your Neo4j connection settings."})

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
    
    # Check for procedure calls that might modify data or expose schema
    if "CALL" in query_upper:
        dangerous_procedures = [
            "apoc.create", "apoc.merge", "apoc.refactor", "apoc.periodic.commit",
            "db.create", "db.drop", "dbms.security"
        ]
        # Block schema access procedures
        schema_procedures = [
            "db.labels", "db.relationshipTypes", "db.schema", "db.propertyKeys",
            "db.constraints", "db.indexes", "apoc.meta"
        ]
        query_lower = cypher_query.lower()
        if any(proc in query_lower for proc in dangerous_procedures):
            return False
        if any(proc in query_lower for proc in schema_procedures):
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
    
    # Test connection first with simple query
    connection_test = _execute_query("RETURN 1 as test")
    test_result = json.loads(connection_test)
    if "error" in test_result:
        return json.dumps({
            "error": "Cannot connect to Neo4j database",
            "details": test_result["error"],
            "suggestion": "Please check your Neo4j connection settings and ensure the database is running."
        })
    
    # Get all node labels
    labels_query = "CALL db.labels() YIELD label RETURN collect(label) as labels"
    
    # Get all relationship types
    rels_query = "CALL db.relationshipTypes() YIELD relationshipType RETURN collect(relationshipType) as relationships"
    
    labels_result = json.loads(_execute_query(labels_query))
    rels_result = json.loads(_execute_query(rels_query))
    
    # Check for errors in results
    if "error" in labels_result:
        return json.dumps({
            "error": "Failed to retrieve database schema",
            "details": labels_result["error"]
        })
    
    # Get sample nodes for each label to understand properties
    schema_info = {
        "labels": labels_result[0]["labels"] if labels_result else [],
        "relationships": rels_result[0]["relationships"] if rels_result else [],
        "node_properties": {}
    }
    
    # For each label, get sample properties (with error handling)
    for label in schema_info["labels"]:
        sample_query = f"MATCH (n:{label}) RETURN n LIMIT 1"
        sample_result = json.loads(_execute_query(sample_query))
        if sample_result and "error" not in sample_result and sample_result:
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
    Returns raw JSON data that can be easily converted to pandas DataFrames for visualization.

    Args:
        cypher_query: The Cypher query to execute (read-only operations only)

    Returns:
        Raw JSON string with query results or error information

    Security:
        Only allows read operations (MATCH, RETURN). Write operations
        (CREATE, MERGE, SET, DELETE) are blocked for safety.
    """
    logger.info(f"Executing tool: execute_cypher_query with query='{cypher_query}'")

    # Enhanced security check: Deep validation of Cypher queries
    if not _validate_query_safety(cypher_query):
        # Check if it's a schema query attempt
        query_lower = cypher_query.lower()
        if any(schema_proc in query_lower for schema_proc in ["db.labels", "db.relationshiptypes", "db.schema", "db.propertykeys", "apoc.meta"]):
            return json.dumps({
                "error": "Direct schema queries are not allowed. Please describe what data you're looking for instead.",
                "suggestion": "For example: 'Show me all customers' or 'What types of relationships exist between customers and orders?'"
            })
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
        
        # Return raw JSON data for code generation
        if isinstance(results, list) and results:
            return json.dumps({
                "data": results,
                "message": "Query executed successfully. Data is ready for visualization.",
                "instructions": "Convert this data to a pandas DataFrame using: df = pd.DataFrame(data['data'])"
            }, indent=2)
        else:
            return json.dumps({"data": [], "message": "No results found."})
            
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

def analyze_graph_paths(start_node_id: str, end_node_id: str, max_hops: int = 3, relationship_types: str = "") -> str:
    """
    Find and analyze paths between two nodes in the graph.
    
    This tool finds the shortest path and optionally all paths between two nodes,
    useful for understanding connections and relationships in your graph.
    
    Args:
        start_node_id: The ID or unique property of the starting node (e.g., "customer:123" or "name:'John'")
        end_node_id: The ID or unique property of the ending node
        max_hops: Maximum number of relationships to traverse (default: 3, max: 5)
        relationship_types: Optional comma-separated list of relationship types to follow (e.g., "KNOWS,WORKS_WITH"). Leave empty for all types.
        
    Returns:
        Formatted results showing paths found, including path length and nodes traversed
    """
    logger.info(f"Executing tool: analyze_graph_paths from '{start_node_id}' to '{end_node_id}'")
    
    # Validate max_hops
    max_hops = min(max_hops, 5)  # Cap at 5 to prevent expensive queries
    
    # Build relationship pattern
    if relationship_types and relationship_types.strip():
        rel_types = relationship_types.split(',')
        rel_pattern = f"[r:{'/'.join(rel_types)}*1..{max_hops}]"
    else:
        rel_pattern = f"[*1..{max_hops}]"
    
    # Parse node identifiers
    def parse_node_id(node_id):
        if ':' in node_id and not node_id.startswith("'"):
            # Format: "Label:id_value"
            label, id_value = node_id.split(':', 1)
            return f"({label} {{id: '{id_value}'}})"
        elif node_id.startswith("id:"):
            # Format: "id:123"
            return f"({{id: '{node_id[3:]}'}})"
        elif ":" in node_id and "'" in node_id:
            # Format: "property:'value'"
            prop, value = node_id.split(':', 1)
            return f"({{{prop}: {value}}})"
        else:
            # Assume it's a simple ID
            return f"({{id: '{node_id}'}})"
    
    start_pattern = parse_node_id(start_node_id)
    end_pattern = parse_node_id(end_node_id)
    
    # Query for shortest path
    shortest_path_query = f"""
    MATCH path = shortestPath({start_pattern}-{rel_pattern}-{end_pattern})
    RETURN length(path) as path_length,
           [n in nodes(path) | labels(n)[0] + ':' + coalesce(n.name, n.id, toString(id(n)))] as nodes,
           [r in relationships(path) | type(r)] as relationships
    """
    
    # Execute shortest path query
    result = execute_cypher_query(shortest_path_query)
    
    # If we found a path and max_hops > 1, also find alternative paths
    if "No results found" not in result and max_hops > 1:
        all_paths_query = f"""
        MATCH path = {start_pattern}-{rel_pattern}-{end_pattern}
        WITH path, length(path) as path_length
        ORDER BY path_length
        LIMIT 5
        RETURN path_length,
               [n in nodes(path) | labels(n)[0] + ':' + coalesce(n.name, n.id, toString(id(n)))] as nodes,
               [r in relationships(path) | type(r)] as relationships
        """
        
        all_paths_result = execute_cypher_query(all_paths_query)
        
        # Combine results
        return f"**Shortest Path:**\n{result}\n\n**Alternative Paths (up to 5):**\n{all_paths_result}"
    
    return result

def calculate_node_centrality(node_label: str = "", centrality_type: str = "degree", limit: int = 10) -> str:
    """
    Calculate centrality metrics for nodes in the graph.
    
    Centrality measures help identify the most important or influential nodes in a network.
    
    Args:
        node_label: Optional node label to filter (e.g., "Customer", "Product"). Leave empty to analyze all nodes.
        centrality_type: Type of centrality to calculate:
            - "degree": Number of direct connections (fastest)
            - "in_degree": Number of incoming connections
            - "out_degree": Number of outgoing connections
            - "betweenness": Nodes that lie on many shortest paths (requires APOC)
            - "pagerank": Importance based on connections (requires APOC)
        limit: Number of top nodes to return (default: 10)
        
    Returns:
        Formatted table of nodes with their centrality scores
    """
    logger.info(f"Executing tool: calculate_node_centrality for {node_label or 'all nodes'} with {centrality_type}")
    
    # Build node pattern
    node_pattern = f"(n:{node_label})" if node_label and node_label.strip() else "(n)"
    
    # Build query based on centrality type
    if centrality_type == "degree":
        query = f"""
        MATCH {node_pattern}
        WITH n, size((n)--()) as degree
        ORDER BY degree DESC
        LIMIT {limit}
        RETURN labels(n)[0] as node_type, 
               coalesce(n.name, n.id, toString(id(n))) as node_identifier,
               degree as centrality_score
        """
    elif centrality_type == "in_degree":
        query = f"""
        MATCH {node_pattern}
        WITH n, size((n)<--()) as in_degree
        ORDER BY in_degree DESC
        LIMIT {limit}
        RETURN labels(n)[0] as node_type,
               coalesce(n.name, n.id, toString(id(n))) as node_identifier,
               in_degree as centrality_score
        """
    elif centrality_type == "out_degree":
        query = f"""
        MATCH {node_pattern}
        WITH n, size((n)-->()) as out_degree
        ORDER BY out_degree DESC
        LIMIT {limit}
        RETURN labels(n)[0] as node_type,
               coalesce(n.name, n.id, toString(id(n))) as node_identifier,
               out_degree as centrality_score
        """
    elif centrality_type == "betweenness":
        # This would require APOC, so we'll simulate with a path-based approach
        query = f"""
        MATCH {node_pattern}
        WITH n
        MATCH path = (a)-[*1..3]-(b)
        WHERE a <> b AND n IN nodes(path)[1..-1]
        WITH n, count(DISTINCT path) as path_count
        ORDER BY path_count DESC
        LIMIT {limit}
        RETURN labels(n)[0] as node_type,
               coalesce(n.name, n.id, toString(id(n))) as node_identifier,
               path_count as centrality_score
        """
    elif centrality_type == "pagerank":
        # Simplified PageRank-like calculation without APOC
        query = f"""
        MATCH {node_pattern}
        WITH n
        MATCH (n)<-[r]-(m)
        WITH n, count(DISTINCT m) as incoming_count, 
             sum(size((m)-->())) as neighbor_connections
        WITH n, incoming_count * 1.0 / (1 + neighbor_connections) as pagerank_estimate
        ORDER BY pagerank_estimate DESC
        LIMIT {limit}
        RETURN labels(n)[0] as node_type,
               coalesce(n.name, n.id, toString(id(n))) as node_identifier,
               round(pagerank_estimate, 4) as centrality_score
        """
    else:
        return json.dumps({
            "error": f"Unknown centrality type: {centrality_type}",
            "suggestion": "Use one of: degree, in_degree, out_degree, betweenness, pagerank"
        })
    
    # Execute query
    result = execute_cypher_query(query)
    
    # Add context to the result
    if "Query Results:" in result:
        return f"**{centrality_type.title()} Centrality Analysis**\n\n{result}\n\n*Higher scores indicate more central/important nodes in the network*"
    
    return result

def detect_communities(node_label: str = "", min_community_size: int = 3) -> str:
    """
    Detect communities or clusters in the graph using connectivity patterns.
    
    Communities are groups of nodes that are more densely connected to each other
    than to nodes outside the group.
    
    Args:
        node_label: Optional node label to analyze (e.g., "Customer"). Leave empty to analyze all nodes.
        min_community_size: Minimum size for a community to be reported (default: 3)
        
    Returns:
        Formatted results showing detected communities and their characteristics
    """
    logger.info(f"Executing tool: detect_communities for {node_label or 'all nodes'}")
    
    # Build node pattern
    node_pattern = f"(n:{node_label})" if node_label and node_label.strip() else "(n)"
    
    # Use a simple community detection approach based on triangles and connected components
    # This finds nodes that form tightly connected groups
    query = f"""
    // Find nodes that form triangles (basic community structure)
    MATCH {node_pattern}-[r1]-(m)-[r2]-(o)-[r3]-(n)
    WHERE id(n) < id(m) AND id(m) < id(o)
    WITH n, m, o, count(*) as triangle_count
    
    // Group nodes that share triangles
    WITH collect(DISTINCT n) + collect(DISTINCT m) + collect(DISTINCT o) as community_nodes
    UNWIND community_nodes as node
    WITH DISTINCT node
    
    // Find all nodes connected to our triangle nodes
    MATCH (node)-[*1..2]-(connected)
    WITH node, collect(DISTINCT connected) as extended_community
    
    // Create community groups
    WITH collect({{anchor: node, members: extended_community}}) as communities
    UNWIND communities as community
    WITH community.anchor as anchor, 
         [n in community.members | n] as members
    WHERE size(members) >= {min_community_size}
    
    // Analyze each community
    WITH anchor, members, size(members) as community_size
    ORDER BY community_size DESC
    LIMIT 10
    
    // Get community details
    UNWIND members as member
    WITH anchor, community_size,
         collect(DISTINCT labels(member)[0]) as node_types,
         count(DISTINCT member) as actual_size,
         collect(DISTINCT coalesce(member.name, member.id, toString(id(member))))[..5] as sample_members
    
    RETURN labels(anchor)[0] + ':' + coalesce(anchor.name, anchor.id, toString(id(anchor))) as community_anchor,
           actual_size as community_size,
           node_types,
           sample_members + CASE WHEN actual_size > 5 THEN ['...'] ELSE [] END as members_sample
    """
    
    # Execute query
    result = execute_cypher_query(query)
    
    # If no communities found with triangles, try a simpler approach
    if "No results found" in result:
        # Fallback: Find highly connected nodes and their neighborhoods
        simpler_query = f"""
        MATCH {node_pattern}
        WITH n, size((n)--()) as degree
        WHERE degree >= 3
        ORDER BY degree DESC
        LIMIT 20
        
        // For each highly connected node, find its neighborhood
        MATCH (n)-[]-(neighbor)
        WITH n, collect(DISTINCT neighbor) as neighbors, degree
        WHERE size(neighbors) >= {min_community_size}
        
        // Check connectivity within neighborhood
        UNWIND neighbors as n1
        UNWIND neighbors as n2
        WHERE id(n1) < id(n2)
        MATCH (n1)-[]-(n2)
        WITH n, neighbors, degree, count(*) as internal_connections
        
        // Calculate density
        WITH n, neighbors, degree, internal_connections,
             2.0 * internal_connections / (size(neighbors) * (size(neighbors) - 1)) as density
        WHERE density > 0.3  // At least 30% connected
        
        RETURN labels(n)[0] + ':' + coalesce(n.name, n.id, toString(id(n))) as community_center,
               size(neighbors) as community_size,
               round(density, 2) as connectivity_density,
               [neighbor in neighbors | coalesce(neighbor.name, neighbor.id, toString(id(neighbor)))][..5] as members_sample
        ORDER BY community_size DESC
        LIMIT 10
        """
        
        result = execute_cypher_query(simpler_query)
        
        if "Query Results:" in result:
            return f"**Community Detection Results**\n*Communities identified by highly connected central nodes*\n\n{result}\n\n*Density indicates how connected members are within the community (0-1)*"
    
    # Add context to the result
    if "Query Results:" in result:
        return f"**Community Detection Results**\n*Communities identified by triangle patterns*\n\n{result}\n\n*Larger communities with diverse node types may indicate important graph structures*"
    
    return result

def find_similar_nodes(reference_node_id: str, node_label: str = "", similarity_type: str = "properties", limit: int = 10) -> str:
    """
    Find nodes similar to a reference node based on properties or connections.
    
    Args:
        reference_node_id: The ID or unique property of the reference node (e.g., "Customer:123" or "name:'John'")
        node_label: Optional label to restrict search (e.g., "Customer"). Leave empty to search all nodes.
        similarity_type: Type of similarity to calculate:
            - "properties": Similar based on shared property values
            - "connections": Similar based on shared relationships
            - "neighborhood": Similar based on common neighbors
        limit: Number of similar nodes to return (default: 10)
        
    Returns:
        Formatted table of similar nodes with similarity scores
    """
    logger.info(f"Executing tool: find_similar_nodes for '{reference_node_id}' using {similarity_type}")
    
    # Parse reference node identifier
    def parse_node_id(node_id):
        if ':' in node_id and not node_id.startswith("'"):
            # Format: "Label:id_value"
            label, id_value = node_id.split(':', 1)
            return f"({label} {{id: '{id_value}'}})", label
        elif ":" in node_id and "'" in node_id:
            # Format: "property:'value'"
            prop, value = node_id.split(':', 1)
            return f"({{{prop}: {value}}})", None
        else:
            # Assume it's a simple ID
            return f"({{id: '{node_id}'}})", None
    
    ref_pattern, ref_label = parse_node_id(reference_node_id)
    search_label = node_label if node_label and node_label.strip() else ref_label
    
    if similarity_type == "properties":
        # Find nodes with similar properties
        query = f"""
        MATCH {ref_pattern} as ref
        WITH ref, keys(ref) as ref_keys, [k in keys(ref) | {{key: k, value: ref[k]}}] as ref_props
        
        MATCH (n{':' + search_label if search_label else ''})
        WHERE id(ref) <> id(n)
        WITH ref, n, ref_props,
             [k in keys(n) WHERE k in keys(ref) | {{key: k, value: n[k]}}] as n_props
        
        // Calculate similarity based on matching property values
        WITH ref, n,
             size([p in ref_props WHERE p in n_props]) as matching_props,
             size(ref_props) as total_props
        WHERE matching_props > 0
        WITH n, matching_props * 1.0 / total_props as similarity
        ORDER BY similarity DESC
        LIMIT {limit}
        
        RETURN labels(n)[0] as node_type,
               coalesce(n.name, n.id, toString(id(n))) as node_identifier,
               round(similarity, 3) as similarity_score,
               matching_props as matching_properties
        """
    
    elif similarity_type == "connections":
        # Find nodes with similar connection patterns
        query = f"""
        MATCH {ref_pattern} as ref
        MATCH (ref)-[]-(ref_connected)
        WITH ref, collect(DISTINCT id(ref_connected)) as ref_connections
        
        MATCH (n{':' + search_label if search_label else ''})
        WHERE id(ref) <> id(n)
        MATCH (n)-[]-(n_connected)
        WITH ref, n, ref_connections, collect(DISTINCT id(n_connected)) as n_connections
        
        // Calculate Jaccard similarity
        WITH n,
             size([x in ref_connections WHERE x in n_connections]) as intersection,
             size(ref_connections + n_connections) as union_size
        WHERE intersection > 0
        WITH n, intersection * 1.0 / union_size as similarity
        ORDER BY similarity DESC
        LIMIT {limit}
        
        RETURN labels(n)[0] as node_type,
               coalesce(n.name, n.id, toString(id(n))) as node_identifier,
               round(similarity, 3) as similarity_score,
               intersection as shared_connections
        """
    
    elif similarity_type == "neighborhood":
        # Find nodes in similar neighborhoods (2-hop similarity)
        query = f"""
        MATCH {ref_pattern} as ref
        MATCH (ref)-[*1..2]-(neighbor)
        WITH ref, collect(DISTINCT id(neighbor)) as ref_neighborhood
        
        MATCH (n{':' + search_label if search_label else ''})
        WHERE id(ref) <> id(n)
        MATCH (n)-[*1..2]-(n_neighbor)
        WITH ref, n, ref_neighborhood, collect(DISTINCT id(n_neighbor)) as n_neighborhood
        
        // Calculate neighborhood overlap
        WITH n,
             size([x in ref_neighborhood WHERE x in n_neighborhood]) as common_neighbors,
             size(ref_neighborhood) + size(n_neighborhood) as total_neighbors
        WHERE common_neighbors > 0
        WITH n, 2.0 * common_neighbors / total_neighbors as similarity
        ORDER BY similarity DESC
        LIMIT {limit}
        
        RETURN labels(n)[0] as node_type,
               coalesce(n.name, n.id, toString(id(n))) as node_identifier,
               round(similarity, 3) as similarity_score,
               common_neighbors
        """
    
    else:
        return json.dumps({
            "error": f"Unknown similarity type: {similarity_type}",
            "suggestion": "Use one of: properties, connections, neighborhood"
        })
    
    # Execute query
    result = execute_cypher_query(query)
    
    # Add context to the result
    if "Query Results:" in result:
        context_map = {
            "properties": "Nodes with similar property values",
            "connections": "Nodes connected to similar entities",
            "neighborhood": "Nodes in similar network neighborhoods"
        }
        return f"**Similarity Analysis: {context_map[similarity_type]}**\n\n{result}\n\n*Higher scores indicate greater similarity (0-1 scale)*"
    
    return result

