#!/bin/bash

# Neo4j ADK Agent Installation Script

echo "🚀 Neo4j ADK Agent Installation"
echo "================================"

# Check if Python 3.11+ is installed
echo "✓ Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
required_version="3.11"

if ! python3 -c "import sys; exit(0 if sys.version_info >= (3,11) else 1)"; then
    echo "❌ Error: Python 3.11 or higher is required. Current version: $python_version"
    exit 1
fi
echo "  Python $python_version detected"

# Check if uv is installed
echo "✓ Checking for uv..."
if ! command -v uv &> /dev/null; then
    echo "❌ Error: uv is not installed. Please install it first:"
    echo "  curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi
echo "  uv is installed"

# Create virtual environment with uv
echo "✓ Creating virtual environment..."
uv venv

# Activate virtual environment
echo "✓ Activating virtual environment..."
source .venv/bin/activate

# Install dependencies
echo "✓ Installing dependencies..."
# Use uv sync to install from pyproject.toml
if [ -f pyproject.toml ]; then
    uv sync
else
    echo "❌ Error: pyproject.toml not found"
    exit 1
fi

# Create .env from example if it doesn't exist
if [ ! -f .env ]; then
    if [ -f .env.example ]; then
        echo "✓ Creating .env file from .env.example..."
        cp .env.example .env
        echo "  ⚠️  Please edit .env with your actual credentials"
    else
        echo "⚠️  No .env file found. Please create one based on the README"
    fi
else
    echo "✓ .env file already exists"
fi

# Verify installation
echo ""
echo "✓ Verifying installation..."
uv run python -c "from google.adk.agents import Agent; print('  ✓ Google ADK installed')"
uv run python -c "import neo4j; print('  ✓ Neo4j driver installed')"
uv run python -c "from dotenv import load_dotenv; print('  ✓ python-dotenv installed')"
uv run python -c "from neo4j_database_agent.agent import root_agent; print('  ✓ Neo4j agent imported successfully')"

echo ""
echo "✅ Installation complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your credentials"
echo "2. Run 'uv run python app.py' to start the deployment interface"
echo "3. Or run 'adk web' to start the agent locally"
echo ""