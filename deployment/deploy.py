#!/usr/bin/env python3
"""
Deployment script for Neo4j Database Agent

This script deploys the Neo4j database agent to Vertex AI Agent Engine
following Google ADK patterns.
"""

import os
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv
import vertexai
from google.cloud import storage
from vertexai import agent_engines
from vertexai.preview.reasoning_engines import AdkApp

# Add the parent directory to the path to import the agent
sys.path.append(str(Path(__file__).parent.parent))

from neo4j_database_agent import root_agent

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """Deploy the Neo4j database agent to Vertex AI Agent Engine."""
    
    # Get required environment variables
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
    location = os.getenv("GOOGLE_CLOUD_LOCATION", "europe-west1")
    staging_bucket = os.getenv("GOOGLE_CLOUD_BUCKET", os.getenv("GOOGLE_CLOUD_STORAGE"))
    
    if not project_id:
        logger.error("GOOGLE_CLOUD_PROJECT environment variable is required")
        sys.exit(1)
    
    if not staging_bucket:
        logger.error("GOOGLE_CLOUD_BUCKET environment variable is required")
        sys.exit(1)
    
    logger.info(f"Deploying Neo4j Database Agent to project: {project_id}")
    logger.info(f"Location: {location}")
    logger.info(f"Staging bucket: {staging_bucket}")
    
    try:
        # Initialize Vertex AI
        vertexai.init(project=project_id, location=location, staging_bucket=staging_bucket)
        
        # Create ADK app with the root agent
        adk_app = AdkApp(
            agent=root_agent,
            enable_tracing=False
        )
        
        # Prepare environment variables for the agent
        env_vars = {
            "NEO4J_URI": os.getenv("NEO4J_URI"),
            "NEO4J_USERNAME": os.getenv("NEO4J_USERNAME"),
            "NEO4J_PASSWORD": os.getenv("NEO4J_PASSWORD"),
            "NEO4J_DATABASE": os.getenv("NEO4J_DATABASE", "neo4j"),
            "MODEL_NAME": os.getenv("MODEL_NAME", "gemini-2.5-flash"),
        }
        
        # Filter out None values
        env_vars = {k: v for k, v in env_vars.items() if v is not None}
        
        logger.info("Creating agent with environment variables...")
        logger.info(f"Environment variables: {list(env_vars.keys())}")
        
        # Deploy the agent
        remote_agent = agent_engines.create(
            adk_app,
            env_vars=env_vars,
            display_name="Neo4j Database Agent",
            description="An agent that helps users query Neo4j databases using natural language"
        )
        
        logger.info(f"Agent deployed successfully!")
        logger.info(f"Agent resource name: {remote_agent.name}")
        
        return remote_agent
        
    except Exception as e:
        logger.error(f"Deployment failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()