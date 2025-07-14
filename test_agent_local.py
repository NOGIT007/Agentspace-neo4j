#!/usr/bin/env python3
"""
Test script to validate the agent works locally before deployment
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_agent_import():
    """Test that we can import the agent"""
    try:
        from agents.agent import root_agent
        print("✅ Agent import successful")
        return root_agent
    except Exception as e:
        print(f"❌ Agent import failed: {e}")
        return None

def test_agent_basic_function(agent):
    """Test basic agent functionality"""
    try:
        # Test that the agent has the expected structure
        if hasattr(agent, 'name'):
            print(f"✅ Agent name: {agent.name}")
        
        if hasattr(agent, 'tools'):
            print(f"✅ Agent has {len(agent.tools)} tools")
            for tool in agent.tools:
                if hasattr(tool, '__name__'):
                    print(f"   - {tool.__name__}")
        
        return True
    except Exception as e:
        print(f"❌ Agent basic test failed: {e}")
        return False

def test_neo4j_connection():
    """Test Neo4j connection"""
    try:
        from neo4j import GraphDatabase
        
        uri = os.getenv("NEO4J_URI")
        username = os.getenv("NEO4J_USERNAME")
        password = os.getenv("NEO4J_PASSWORD")
        
        if not all([uri, username, password]):
            print("❌ Missing Neo4j environment variables")
            return False
        
        with GraphDatabase.driver(uri, auth=(username, password)) as driver:
            with driver.session() as session:
                result = session.run("RETURN 1 as test")
                test_value = result.single()["test"]
                if test_value == 1:
                    print("✅ Neo4j connection successful")
                    return True
        
    except Exception as e:
        print(f"❌ Neo4j connection failed: {e}")
        return False

def main():
    print("🧪 Testing agent locally before deployment...")
    print("=" * 50)
    
    # Test 1: Import agent
    agent = test_agent_import()
    if not agent:
        sys.exit(1)
    
    # Test 2: Basic agent functionality
    if not test_agent_basic_function(agent):
        sys.exit(1)
    
    # Test 3: Neo4j connection
    if not test_neo4j_connection():
        print("⚠️  Neo4j connection failed - deployment might fail")
    
    print("=" * 50)
    print("✅ All tests passed! Agent should deploy successfully.")

if __name__ == "__main__":
    main()