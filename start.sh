#!/bin/bash

echo "🚀 Starting Agent Manager..."
echo "📍 Make sure you have:"
echo "   - Configured your .env file"
echo "   - Authenticated with: gcloud auth application-default login"
echo ""

# Run with uv
uv run python app.py