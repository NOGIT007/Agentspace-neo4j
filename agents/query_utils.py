"""
Utility functions for common Neo4j query patterns.
These functions help build common Cypher query components for time-based, aggregation, and calculation queries.
"""

from typing import Dict, List, Optional
import re

def build_time_filter(period: str, date_property: str = "date") -> str:
    """
    Generate time-based WHERE clauses for common time periods.
    
    Args:
        period: Time period ('today', 'yesterday', 'last_week', 'last_month', 'this_year', etc.)
        date_property: The property name containing the date (default: 'date')
        
    Returns:
        A WHERE clause string for the specified time period
    """
    period = period.lower().replace(' ', '_')
    
    time_filters = {
        'today': f"date({date_property}) = date()",
        'yesterday': f"date({date_property}) = date() - duration('P1D')",
        'last_week': f"{date_property} >= date() - duration('P7D')",
        'last_month': f"{date_property} >= date() - duration('P1M')",
        'this_week': f"{date_property} >= date() - duration('P' + str(date().weekday()) + 'D')",
        'this_month': f"date.truncate('month', {date_property}) = date.truncate('month', date())",
        'this_year': f"date.truncate('year', {date_property}) = date.truncate('year', date())",
        'last_year': f"date.truncate('year', {date_property}) = date.truncate('year', date() - duration('P1Y'))"
    }
    
    return time_filters.get(period, f"{date_property} >= date() - duration('P7D')")  # Default to last week

def build_aggregation_query(
    node_label: str, 
    group_by: str, 
    metric: str, 
    aggregation_func: str = "count",
    order_desc: bool = True,
    limit: Optional[int] = None
) -> str:
    """
    Generate aggregation queries with GROUP BY functionality.
    
    Args:
        node_label: The node label to query (e.g., 'Customer', 'Product')
        group_by: The property to group by (e.g., 'city', 'category')
        metric: The metric to aggregate (e.g., 'price', 'amount', or '*' for count)
        aggregation_func: The aggregation function ('count', 'sum', 'avg', 'max', 'min')
        order_desc: Whether to order results in descending order
        limit: Optional limit for results
        
    Returns:
        A complete Cypher query string
    """
    # Handle count aggregation specially
    if aggregation_func == "count":
        if metric == "*" or metric == node_label.lower():
            agg_expr = f"count(n) as {aggregation_func}_{metric.replace('*', 'total')}"
        else:
            agg_expr = f"count(n.{metric}) as {aggregation_func}_{metric}"
    else:
        agg_expr = f"{aggregation_func}(n.{metric}) as {aggregation_func}_{metric}"
    
    order_direction = "DESC" if order_desc else "ASC"
    order_clause = f"ORDER BY {aggregation_func}_{metric.replace('*', 'total')} {order_direction}"
    
    limit_clause = f"LIMIT {limit}" if limit else ""
    
    query = f"""
MATCH (n:{node_label})
RETURN n.{group_by}, {agg_expr}
{order_clause}
{limit_clause}
""".strip()
    
    return query

def build_grand_total_query(
    node_label: str,
    group_by_property: str,
    metric_property: str,
    aggregation_func: str = "sum",
    order_desc: bool = True
) -> str:
    """
    Generate queries that show individual values alongside grand totals.
    
    Args:
        node_label: The node label to query
        group_by_property: Property to group by (e.g., 'name', 'category')
        metric_property: The metric to aggregate (e.g., 'mrr', 'amount')
        aggregation_func: The aggregation function ('sum', 'avg', 'count')
        order_desc: Whether to order results in descending order
        
    Returns:
        A complete Cypher query that shows both details and grand total
    """
    order_direction = "DESC" if order_desc else "ASC"
    
    query = f"""
MATCH (n:{node_label})
WITH n.{group_by_property} as item, {aggregation_func}(n.{metric_property}) as individual_value
WITH collect({{item: item, value: individual_value}}) as details, {aggregation_func}(individual_value) as grand_total
UNWIND details as detail
RETURN detail.item as {group_by_property.title()}, 
       detail.value as {metric_property.upper()}, 
       grand_total as GrandTotal{metric_property.upper()}
ORDER BY detail.value {order_direction}
""".strip()
    
    return query

def build_date_aggregation_query(
    node_label: str,
    date_property: str,
    metric_property: str,
    aggregation_func: str = "sum",
    period: str = "month"
) -> str:
    """
    Generate queries for aggregating data by time periods.
    
    Args:
        node_label: The node label to query
        date_property: The date property name
        metric_property: The metric to aggregate (e.g., 'amount', 'price')
        aggregation_func: The aggregation function ('sum', 'avg', 'count', 'max', 'min')
        period: Time period for grouping ('day', 'week', 'month', 'year')
        
    Returns:
        A complete Cypher query string for time-based aggregation
    """
    query = f"""
MATCH (n:{node_label})
RETURN date.truncate('{period}', n.{date_property}) as {period}, 
       {aggregation_func}(n.{metric_property}) as total_{metric_property}
ORDER BY {period}
""".strip()
    
    return query

def validate_query_safety(cypher: str) -> bool:
    """
    Deep validation of Cypher queries for safety.
    
    Args:
        cypher: The Cypher query to validate
        
    Returns:
        True if the query is safe to execute, False otherwise
    """
    if not cypher:
        return False
    
    # Normalize query for analysis
    query_upper = cypher.upper().strip()
    query_lower = cypher.lower().strip()
    
    # Allowed read-only keywords
    allowed_keywords = [
        "MATCH", "RETURN", "WHERE", "WITH", "ORDER", "BY", "LIMIT", "SKIP",
        "AS", "AND", "OR", "NOT", "IN", "CONTAINS", "STARTS", "ENDS",
        "COUNT", "SUM", "AVG", "MAX", "MIN", "COLLECT", "DISTINCT",
        "CASE", "WHEN", "THEN", "ELSE", "END", "COALESCE", "HEAD", "TAIL",
        "SIZE", "LENGTH", "TRIM", "UPPER", "LOWER", "SPLIT", "SUBSTRING",
        "DATE", "TIME", "DATETIME", "DURATION", "TRUNCATE"
    ]
    
    # Extract all words from the query
    words = re.findall(r'\b[A-Z_]+\b', query_upper)
    
    # Check if all words are in the allowed list or are identifiers
    for word in words:
        if word not in allowed_keywords and not _is_identifier(word):
            # Check for dangerous operations
            if word in ["CREATE", "MERGE", "SET", "DELETE", "REMOVE", "DROP", "DETACH"]:
                return False
    
    # Check for procedure calls
    if "CALL" in query_upper:
        # Only allow safe read-only procedures
        safe_procedures = [
            "db.labels", "db.relationshiptypes", "db.schema", "db.propertykeys",
            "apoc.meta", "apoc.help", "dbms.procedures", "dbms.functions"
        ]
        
        # Extract procedure names
        proc_pattern = r'CALL\s+([a-zA-Z0-9_.]+)'
        procedures = re.findall(proc_pattern, query_lower)
        
        for proc in procedures:
            if not any(safe_proc in proc for safe_proc in safe_procedures):
                return False
    
    return True

def _is_identifier(word: str) -> bool:
    """
    Check if a word is likely an identifier (node label, property name, etc.)
    
    Args:
        word: The word to check
        
    Returns:
        True if the word looks like an identifier
    """
    # Identifiers typically start with a letter and contain letters, numbers, underscores
    return bool(re.match(r'^[A-Z][A-Z0-9_]*$', word))

def build_relationship_query(
    start_label: str,
    relationship_type: str,
    end_label: str,
    return_properties: List[str] = None,
    limit: Optional[int] = 20
) -> str:
    """
    Build queries for exploring relationships between nodes.
    
    Args:
        start_label: Starting node label
        relationship_type: The relationship type
        end_label: Ending node label
        return_properties: List of properties to return
        limit: Limit for results
        
    Returns:
        A complete Cypher query for relationship exploration
    """
    if return_properties is None:
        return_properties = ["*"]
    
    if return_properties == ["*"]:
        return_clause = "s, r, e"
    else:
        props = ", ".join([f"s.{prop}" for prop in return_properties if prop.startswith('s.')] +
                         [f"e.{prop}" for prop in return_properties if prop.startswith('e.')])
        return_clause = props if props else "s, r, e"
    
    limit_clause = f"LIMIT {limit}" if limit else ""
    
    query = f"""
MATCH (s:{start_label})-[r:{relationship_type}]->(e:{end_label})
RETURN {return_clause}
{limit_clause}
""".strip()
    
    return query

def suggest_query_optimization(cypher: str) -> List[str]:
    """
    Provide suggestions for optimizing Cypher queries.
    
    Args:
        cypher: The Cypher query to analyze
        
    Returns:
        List of optimization suggestions
    """
    suggestions = []
    query_lower = cypher.lower()
    
    # Check for missing LIMIT
    if "limit" not in query_lower and "count(" not in query_lower:
        suggestions.append("Consider adding LIMIT clause to prevent large result sets")
    
    # Check for inefficient patterns
    if "match (n)" in query_lower and "where" not in query_lower:
        suggestions.append("Consider adding WHERE clause to filter results")
    
    # Check for missing indexes hints
    if re.search(r'where\s+\w+\.\w+\s*=', query_lower):
        suggestions.append("Ensure indexes exist on filtered properties for better performance")
    
    # Check for complex aggregations without grouping
    agg_functions = ["sum", "avg", "count", "max", "min"]
    if any(func in query_lower for func in agg_functions) and "group by" not in query_lower:
        suggestions.append("Consider using WITH clause for complex aggregations")
    
    return suggestions