#!/bin/bash
# Installation script for GitHub PR Analyzer & Executive Summary Generator

set -e

echo "🚀 Installing GitHub PR Analyzer & Executive Summary Generator"
echo "================================================================"

# Check if Python 3.8+ is available
python_version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
required_version="3.8"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ Error: Python 3.8 or higher is required. Found: $python_version"
    exit 1
fi

echo "✅ Python version: $python_version"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️ Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📚 Installing dependencies..."
pip install -r requirements.txt

# Install the package in development mode
echo "🔗 Installing package in development mode..."
pip install -e .

echo ""
echo "✅ Installation completed successfully!"
echo ""
echo "📋 Next steps:"
echo "1. Set up your environment variables:"
echo "   export GITHUB_TOKEN=your_github_token"
echo "   export OPENAI_API_KEY=your_openai_api_key"
echo "   export SLACK_BOT_TOKEN=your_slack_bot_token (optional)"
echo "   export SLACK_CHANNEL_ID=your_slack_channel_id (optional)"
echo "   export LINEAR_API_KEY=your_linear_api_key (optional)"
echo ""
echo "2. Activate the virtual environment:"
echo "   source venv/bin/activate"
echo ""
echo "3. Run the tools:"
echo "   python github_pr_analyzer.py DrivetrainAi/drive --send-to-slack"
echo "   python chunked_summarizer.py document.txt"
echo ""
echo "📖 For more information, see README.md" 