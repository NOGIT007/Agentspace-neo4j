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
uv pip install -r <(grep -v '^\s*#' pyproject.toml | grep -A 100 'dependencies = \[' | grep -B 100 '\]' | grep '"' | sed 's/[",]//g' | sed 's/^[[:space:]]*//')

# Install neo4j driver specifically
echo "✓ Ensuring Neo4j driver is installed..."
uv pip install neo4j

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
python3 -c "from google.adk.agents import LlmAgent; print('  ✓ Google ADK installed')"
python3 -c "import neo4j; print('  ✓ Neo4j driver installed')"
python3 -c "from dotenv import load_dotenv; print('  ✓ python-dotenv installed')"

echo ""
echo "✅ Installation complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your credentials"
echo "2. Run 'source .venv/bin/activate' to activate the environment"
echo "3. Run 'adk web' to start the agent locally"
echo ""