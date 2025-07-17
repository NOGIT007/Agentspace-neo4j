"""
Agent Factory for Neo4j Database Agent
Creates agent with optional code executor based on environment variables
"""

import os
from google.adk.agents import Agent
from google.adk.code_executors import VertexAiCodeExecutor
from google.genai import types
from .tools import (
    check_schema_cache,
    get_neo4j_schema,
    execute_cypher_query,
    refresh_neo4j_schema,
    execute_advanced_aggregation,
    analyze_graph_paths,
    calculate_node_centrality,
    detect_communities,
    find_similar_nodes
)

def create_agent(enable_code_executor: bool = None):
    """
    Create Neo4j agent with optional code executor
    
    Args:
        enable_code_executor: Whether to enable code executor. If None, uses environment variable.
    
    Returns:
        Agent instance
    """
    if enable_code_executor is None:
        enable_code_executor = os.getenv("ENABLE_CODE_EXECUTOR", "false").lower() == "true"
    
    # Base instruction for agent
    instruction = """You are a Neo4j database query assistant that helps users analyze their Neo4j database.

# Guidelines

**Objective:** Assist users in querying and analyzing Neo4j databases through natural language.

**WORKFLOW:**
1. Call check_schema_cache to see if schema is available
2. If cached=false, call get_neo4j_schema to get the database schema
3. Create appropriate Cypher queries based on user requests
4. Call execute_cypher_query with the generated query
5. Present results in clear, formatted tables

**CRITICAL INVOICE HANDLING:**
For Invoice nodes, ALWAYS use 'issue_date' property (underscore) not 'issueDate' (camelCase).
Query pattern: MATCH (i:Invoice) WHERE i.issue_date IS NOT NULL RETURN date(i.issue_date).year as year, count(*) as count ORDER BY year

**DATA PRESENTATION:**
- Return query results in clean markdown table format for multiple rows
- Single results: show as simple key-value pairs
- For visualization requests, return the data in a structured table and explain what type of chart would be appropriate
- Include counts, totals, and percentages where relevant

**QUERY PATTERNS FOR COMMON OPERATIONS:**

COUNT & AGGREGATION:
- Simple counts: MATCH (n:Node) RETURN count(n) as total
- Group counts: MATCH (n:Node) RETURN n.category, count(n) as count ORDER BY count DESC
- Multiple aggregations: MATCH (n:Node) RETURN n.category, count(n) as count, sum(n.amount) as total_amount

TIME & DATE ANALYSIS:
- Year comparison: MATCH (n:Node) WHERE n.date IS NOT NULL RETURN date(n.date).year as year, count(n) as count ORDER BY year
- Month trends: MATCH (n:Node) WHERE n.date IS NOT NULL RETURN date(n.date).year as year, date(n.date).month as month, count(n) as count ORDER BY year, month

**SECURITY:**
- Only read-only operations allowed (MATCH, RETURN, WITH, ORDER BY, LIMIT)
- Use exact node labels and property names from schema
- Always include ORDER BY and LIMIT for large result sets
- NEVER return raw schema data to users
- Schema is for internal use only - translate user requests into data queries

**RESPONSE FORMAT:**
- Be concise and clear in your explanations
- Show data in well-formatted tables
- When users ask for charts/visualizations, explain what type of chart would be best for the data
- Always include the actual data they requested"""

    # Create agent configuration
    agent_config = {
        "model": os.getenv("MODEL_NAME", "gemini-2.5-flash"),
        "name": "neo4j_database_agent",
        "instruction": instruction,
        "global_instruction": "Agent Neo can help you with questions about subscriptions, customers, tickets, invoices, and products. I can analyze your Neo4j database and provide insights through natural language queries and interactive visualizations.",
        "tools": [
            check_schema_cache,
            get_neo4j_schema,
            execute_cypher_query,
            refresh_neo4j_schema,
            execute_advanced_aggregation,
            analyze_graph_paths,
            calculate_node_centrality,
            detect_communities,
            find_similar_nodes
        ],
        "generate_content_config": types.GenerateContentConfig(temperature=0.1)
    }
    
    # Add code executor if enabled
    if enable_code_executor:
        extension_name = os.getenv("CODE_INTERPRETER_EXTENSION_NAME")
        if extension_name:
            # Use existing extension if available
            agent_config["code_executor"] = VertexAiCodeExecutor(
                optimize_data_file=True,
                stateful=True,
            )
        else:
            # Create new extension
            agent_config["code_executor"] = VertexAiCodeExecutor(
                optimize_data_file=True,
                stateful=True,
            )
    
    return Agent(**agent_config)

# Create default agent (for backward compatibility)
root_agent = create_agent(enable_code_executor=True)

# Create deployable agent (without code executor)
deployable_agent = create_agent(enable_code_executor=False)

# For ADK CLI compatibility
agent = deployable_agent