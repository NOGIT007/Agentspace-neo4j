"""
Simple chart generation for Neo4j query results
Creates basic ASCII charts without external dependencies
"""

import json
from typing import List, Dict, Any

def create_bar_chart(data: List[Dict[str, Any]], title: str = "Data Visualization") -> str:
    """
    Create a simple ASCII bar chart from query results.
    
    Args:
        data: List of dictionaries with query results
        title: Chart title
        
    Returns:
        ASCII bar chart string
    """
    if not data:
        return "No data to visualize"
    
    # Try to find label and value columns
    first_row = data[0]
    keys = list(first_row.keys())
    
    # Find numeric column for values (prefer 'count', 'total', 'amount', etc.)
    value_key = None
    label_key = None
    
    # Priority order for value columns
    value_priorities = ['count', 'total', 'amount', 'sum', 'value', 'number']
    
    for priority in value_priorities:
        if priority in keys:
            try:
                # Test if all values in this column are numeric
                all_numeric = all(isinstance(row.get(priority), (int, float)) for row in data)
                if all_numeric:
                    value_key = priority
                    break
            except:
                continue
    
    # If no priority match, find any numeric column
    if not value_key:
        for key in keys:
            try:
                # Test if all values in this column are numeric
                all_numeric = all(isinstance(row.get(key), (int, float)) for row in data)
                if all_numeric:
                    value_key = key
                    break
            except:
                continue
    
    # Find label column (prefer 'year', 'name', 'label', then first non-numeric column)
    label_priorities = ['year', 'name', 'label', 'category', 'type']
    
    for priority in label_priorities:
        if priority in keys and priority != value_key:
            label_key = priority
            break
    
    # If no priority match, find any non-numeric column
    if not label_key:
        for key in keys:
            if key != value_key:
                label_key = key
                break
    
    if not value_key or not label_key:
        return "Cannot create chart - need label and numeric columns"
    
    # Extract data
    chart_data = []
    max_value = 0
    for row in data:
        label = str(row.get(label_key, 'Unknown'))
        value = float(row.get(value_key, 0))
        max_value = max(max_value, value)
        chart_data.append((label, value))
    
    # Sort by label (for year data)
    try:
        chart_data.sort(key=lambda x: int(x[0]) if x[0].isdigit() else x[0])
    except:
        pass
    
    # Create chart
    output = [title, "=" * len(title), ""]
    
    bar_width = 40
    for label, value in chart_data:
        if max_value > 0:
            bar_length = int((value / max_value) * bar_width)
        else:
            bar_length = 0
        
        bar = "█" * bar_length
        spaces = " " * (bar_width - bar_length)
        
        # Format value
        value_str = f"{value:,.0f}" if value == int(value) else f"{value:.1f}"
        
        # Truncate label if too long
        display_label = label[:12] + "..." if len(label) > 15 else label
        
        output.append(f"{display_label:15s} : {bar}{spaces} {value_str}")
    
    # Add total
    total = sum(v for _, v in chart_data)
    total_str = f"{total:,.0f}" if total == int(total) else f"{total:.1f}"
    output.append("")
    output.append(f"{'Total':15s} : {total_str}")
    
    return "\n".join(output)

def format_as_chart(query_results_json: str) -> str:
    """
    Format query results as a chart.
    
    Args:
        query_results_json: JSON string from execute_cypher_query
        
    Returns:
        Formatted chart string
    """
    try:
        results = json.loads(query_results_json)
        
        # Handle error responses
        if isinstance(results, dict) and "error" in results:
            return f"Error: {results['error']}"
        
        # Ensure results is a list
        if not isinstance(results, list):
            results = [results] if results else []
        
        if not results:
            return "No data to visualize"
        
        # Create chart
        return create_bar_chart(results)
        
    except json.JSONDecodeError:
        return "Error: Invalid JSON in query results"
    except Exception as e:
        return f"Error creating chart: {str(e)}"