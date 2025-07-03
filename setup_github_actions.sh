#!/bin/bash
# GitHub Actions PR Summary Setup Script

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 GitHub Actions PR Summary Setup${NC}"
echo "=========================================="

# Check if we're in a git repository
if [ ! -d ".git" ]; then
    echo -e "${RED}❌ This script must be run from a git repository${NC}"
    exit 1
fi

# Check if workflow file exists
if [ ! -f ".github/workflows/pr-summary-slack.yml" ]; then
    echo -e "${RED}❌ Workflow file not found. Please ensure .github/workflows/pr-summary-slack.yml exists${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Found workflow file${NC}"

# Create .github directory if it doesn't exist
mkdir -p .github/workflows

echo -e "\n${YELLOW}📋 Setup Checklist${NC}"
echo "=================="
echo -e "${BLUE}1. GitHub Repository Secrets${NC}"
echo "   Go to: https://github.com/$(git remote get-url origin | sed 's/.*github.com[:/]\([^/]*\/[^/]*\).*/\1/' | sed 's/\.git$//')/settings/secrets/actions"
echo ""
echo -e "${YELLOW}Required secrets:${NC}"
echo "   • OPENAI_API_KEY: Your OpenAI API key"
echo "   • SLACK_BOT_TOKEN: Your Slack bot token (xoxb-...)"
echo "   • SLACK_CHANNEL_ID: Your Slack channel ID (C...)"
echo ""

echo -e "${BLUE}2. Slack App Setup${NC}"
echo "   Go to: https://api.slack.com/apps"
echo "   Create a new app with these scopes:"
echo "   • chat:write"
echo "   • chat:write.public"
echo ""

echo -e "${BLUE}3. Test the Workflow${NC}"
echo "   After setting up secrets, test with manual trigger:"
echo "   • Go to Actions tab in your repository"
echo "   • Select 'PR Summary to Slack'"
echo "   • Click 'Run workflow'"
echo ""

# Ask for configuration
echo -e "${YELLOW}🔧 Configuration${NC}"
echo "================"

read -p "Repository to analyze (e.g., DrivetrainAi/drive): " REPO
read -p "Default time range (1w, 1m, 6m, 1y) [default: 1w]: " TIME_RANGE
TIME_RANGE=${TIME_RANGE:-1w}

read -p "Default branches (comma-separated) [default: main-v2,main-v3]: " BRANCHES
BRANCHES=${BRANCHES:-main-v2,main-v3}

read -p "Schedule (cron format) [default: '0 9 * * 1' for Mondays at 9 AM]: " CRON_SCHEDULE
CRON_SCHEDULE=${CRON_SCHEDULE:-'0 9 * * 1'}

# Update workflow file with custom values
echo -e "\n${YELLOW}📝 Updating workflow file...${NC}"

# Create a backup
cp .github/workflows/pr-summary-slack.yml .github/workflows/pr-summary-slack.yml.backup

# Update the workflow file
sed -i.bak "s/DrivetrainAi\/drive/$REPO/g" .github/workflows/pr-summary-slack.yml
sed -i.bak "s/default: '1w'/$TIME_RANGE/g" .github/workflows/pr-summary-slack.yml
sed -i.bak "s/default: 'main-v2,main-v3'/$BRANCHES/g" .github/workflows/pr-summary-slack.yml
sed -i.bak "s/cron: '0 9 \* \* 1'/cron: '$CRON_SCHEDULE'/g" .github/workflows/pr-summary-slack.yml

# Clean up backup files
rm .github/workflows/pr-summary-slack.yml.bak

echo -e "${GREEN}✅ Workflow file updated${NC}"

# Create a test script
TEST_SCRIPT="test_workflow.sh"
echo -e "\n${YELLOW}📜 Creating test script...${NC}"

cat > "$TEST_SCRIPT" << EOF
#!/bin/bash
# Test script for GitHub Actions workflow

echo "🧪 Testing GitHub Actions workflow..."

# Check if we're in a git repository
if [ ! -d ".git" ]; then
    echo "❌ Not in a git repository"
    exit 1
fi

# Get repository URL
REPO_URL=\$(git remote get-url origin | sed 's/.*github.com[:/]\([^/]*\/[^/]*\).*/\1/' | sed 's/\.git$//')
echo "📁 Repository: \$REPO_URL"

# Check if workflow file exists
if [ ! -f ".github/workflows/pr-summary-slack.yml" ]; then
    echo "❌ Workflow file not found"
    exit 1
fi

echo "✅ Workflow file found"

# Check secrets (basic check)
echo "🔐 Checking secrets..."
echo "   Note: You need to manually verify these in GitHub repository settings"
echo "   Required secrets:"
echo "   • OPENAI_API_KEY"
echo "   • SLACK_BOT_TOKEN" 
echo "   • SLACK_CHANNEL_ID"

echo ""
echo "🎯 Next steps:"
echo "1. Go to: https://github.com/\$REPO_URL/settings/secrets/actions"
echo "2. Add the required secrets"
echo "3. Go to: https://github.com/\$REPO_URL/actions"
echo "4. Select 'PR Summary to Slack' workflow"
echo "5. Click 'Run workflow' to test"
echo ""
echo "📅 Schedule: $CRON_SCHEDULE"
echo "📊 Repository: $REPO"
echo "⏰ Time Range: $TIME_RANGE"
echo "🌿 Branches: $BRANCHES"
EOF

chmod +x "$TEST_SCRIPT"
echo -e "${GREEN}✅ Created $TEST_SCRIPT${NC}"

# Create a secrets template
SECRETS_TEMPLATE="secrets_template.md"
echo -e "\n${YELLOW}📋 Creating secrets template...${NC}"

cat > "$SECRETS_TEMPLATE" << EOF
# GitHub Secrets Setup Guide

## Required Secrets

Add these secrets to your GitHub repository:
Settings → Secrets and variables → Actions

### 1. OPENAI_API_KEY
- **Value**: Your OpenAI API key
- **Format**: sk-...
- **Source**: https://platform.openai.com/api-keys

### 2. SLACK_BOT_TOKEN
- **Value**: Your Slack bot token
- **Format**: xoxb-...
- **Source**: https://api.slack.com/apps → Your App → OAuth & Permissions

### 3. SLACK_CHANNEL_ID
- **Value**: Your Slack channel ID
- **Format**: C...
- **Source**: Right-click channel in Slack → Copy link → Extract ID

## How to Get Slack Credentials

1. **Create Slack App**:
   - Go to https://api.slack.com/apps
   - Click "Create New App" → "From scratch"
   - Name: "GitHub PR Reporter"
   - Select your workspace

2. **Configure Scopes**:
   - Go to "OAuth & Permissions"
   - Add scopes:
     - \`chat:write\`
     - \`chat:write.public\`
   - Install app to workspace
   - Copy "Bot User OAuth Token"

3. **Get Channel ID**:
   - In Slack, right-click channel → "Copy link"
   - Channel ID is the last part of URL

## Test Your Setup

Run: \`./test_workflow.sh\`

Then manually trigger the workflow in GitHub Actions.
EOF

echo -e "${GREEN}✅ Created $SECRETS_TEMPLATE${NC}"

echo -e "\n${GREEN}🎉 Setup Complete!${NC}"
echo "=================="
echo -e "${BLUE}📁 Files created:${NC}"
echo "  • .github/workflows/pr-summary-slack.yml (updated)"
echo "  • test_workflow.sh (test script)"
echo "  • secrets_template.md (setup guide)"
echo ""
echo -e "${YELLOW}🔧 Next steps:${NC}"
echo "1. Review $SECRETS_TEMPLATE for secrets setup"
echo "2. Run ./test_workflow.sh to verify setup"
echo "3. Add secrets to GitHub repository"
echo "4. Test with manual workflow trigger"
echo "5. Monitor the first scheduled run"
echo ""
echo -e "${BLUE}📊 Configuration:${NC}"
echo "  • Repository: $REPO"
echo "  • Time Range: $TIME_RANGE"
echo "  • Branches: $BRANCHES"
echo "  • Schedule: $CRON_SCHEDULE"
echo ""
echo -e "${GREEN}✅ Your GitHub Actions workflow is ready!${NC}" 