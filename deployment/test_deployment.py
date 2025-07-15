#!/usr/bin/env python3
"""
Test script for deployed Neo4j ADK Agent
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_deployed_agent():
    """Test the deployed Neo4j agent"""
    
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
    location = os.getenv("GOOGLE_CLOUD_LOCATION", "europe-west1")
    
    if not project_id:
        raise ValueError("GOOGLE_CLOUD_PROJECT environment variable is required")
    
    print(f"Testing deployed Neo4j Agent...")
    print(f"Project: {project_id}")
    print(f"Location: {location}")
    
    try:
        # Test queries using ADK CLI
        test_queries = [
            "How many invoices each year?",
            "List all customers",
            "Show me the database schema"
        ]
        
        print("\n🧪 Testing deployed agent with sample queries...")
        
        import subprocess
        
        for query in test_queries:
            print(f"\n📝 Query: {query}")
            try:
                # Use ADK CLI to test the deployed agent
                cmd = [
                    "adk", "run",
                    "--project", project_id,
                    "--location", location,
                    "--query", query
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode == 0:
                    print(f"✅ Response: {result.stdout}")
                else:
                    print(f"❌ Query failed: {result.stderr}")
                    
            except Exception as e:
                print(f"❌ Query failed: {e}")
        
        print("\n✅ Deployment test completed")
        
    except Exception as e:
        print(f"❌ Deployment test failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    test_deployed_agent()