#!/bin/bash

echo "🚀 Starting Agent Manager..."
echo "📍 Make sure you have:"
echo "   - Configured your .env file"
echo "   - Authenticated with: gcloud auth application-default login"
echo ""
echo "🌐 Web UI will be available at: http://localhost:5001"
echo ""

# Run with uv
uv run python app.py