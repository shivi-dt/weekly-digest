#!/bin/bash
# Setup Cron Jobs for GitHub PR Slack Reporting

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 GitHub PR Slack Reporter - Cron Setup${NC}"
echo "=================================================="

# Get current directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SLACK_REPORTER="$SCRIPT_DIR/slack_pr_reporter.py"

# Check if script exists
if [ ! -f "$SLACK_REPORTER" ]; then
    echo -e "${RED}❌ slack_pr_reporter.py not found in $SCRIPT_DIR${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Found slack_pr_reporter.py${NC}"

# Get configuration
echo -e "\n${YELLOW}📝 Configuration Setup${NC}"
echo "------------------------"

read -p "Enter repository name (e.g., DrivetrainAi/drive): " REPO
read -p "Enter Slack webhook URL: " SLACK_WEBHOOK
read -p "Enter time range for reports (1w, 1m, 6m, 1y) [default: 1w]: " TIME_RANGE
TIME_RANGE=${TIME_RANGE:-1w}

read -p "Enter branches to analyze (space-separated) [default: main-v2 main-v3]: " BRANCHES
BRANCHES=${BRANCHES:-main-v2 main-v3}

# Create environment file
ENV_FILE="$SCRIPT_DIR/.env"
echo -e "\n${YELLOW}🔧 Creating environment file...${NC}"

cat > "$ENV_FILE" << EOF
# GitHub PR Slack Reporter Environment Variables
GITHUB_TOKEN=your_github_token_here
OPENAI_API_KEY=your_openai_api_key_here
SLACK_WEBHOOK_URL=$SLACK_WEBHOOK
REPO=$REPO
TIME_RANGE=$TIME_RANGE
BRANCHES=$BRANCHES
EOF

echo -e "${GREEN}✅ Created $ENV_FILE${NC}"
echo -e "${YELLOW}⚠️  Please edit $ENV_FILE and add your actual tokens${NC}"

# Create the cron script
CRON_SCRIPT="$SCRIPT_DIR/run_slack_report.sh"
echo -e "\n${YELLOW}📜 Creating cron execution script...${NC}"

cat > "$CRON_SCRIPT" << 'EOF'
#!/bin/bash
# Cron script for GitHub PR Slack reporting

# Load environment variables
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/.env"

# Activate virtual environment if it exists
if [ -d "$SCRIPT_DIR/venv" ]; then
    source "$SCRIPT_DIR/venv/bin/activate"
fi

# Run the Slack reporter
cd "$SCRIPT_DIR"
python slack_pr_reporter.py "$REPO" \
    --time-range "$TIME_RANGE" \
    --branches $BRANCHES \
    --slack-webhook "$SLACK_WEBHOOK_URL" \
    >> "$SCRIPT_DIR/slack_reports.log" 2>&1

echo "$(date): PR report completed" >> "$SCRIPT_DIR/slack_reports.log"
EOF

chmod +x "$CRON_SCRIPT"
echo -e "${GREEN}✅ Created $CRON_SCRIPT${NC}"

# Create log file
touch "$SCRIPT_DIR/slack_reports.log"
echo -e "${GREEN}✅ Created log file${NC}"

# Show cron options
echo -e "\n${BLUE}⏰ Cron Job Options${NC}"
echo "=================="
echo -e "${YELLOW}1. Weekly Report (Every Monday at 9 AM)${NC}"
echo "   0 9 * * 1 $CRON_SCRIPT"
echo ""
echo -e "${YELLOW}2. Daily Report (Every day at 9 AM)${NC}"
echo "   0 9 * * * $CRON_SCRIPT"
echo ""
echo -e "${YELLOW}3. Bi-weekly Report (Every 2 weeks on Monday)${NC}"
echo "   0 9 * * 1 $CRON_SCRIPT"
echo ""

# Ask user for preference
echo -e "${YELLOW}Select cron schedule:${NC}"
echo "1. Weekly (recommended)"
echo "2. Daily"
echo "3. Bi-weekly"
echo "4. Custom"
read -p "Enter choice (1-4): " CRON_CHOICE

case $CRON_CHOICE in
    1)
        CRON_SCHEDULE="0 9 * * 1"
        SCHEDULE_NAME="Weekly (Mondays at 9 AM)"
        ;;
    2)
        CRON_SCHEDULE="0 9 * * *"
        SCHEDULE_NAME="Daily (9 AM)"
        ;;
    3)
        CRON_SCHEDULE="0 9 * * 1"
        SCHEDULE_NAME="Bi-weekly (Mondays at 9 AM)"
        ;;
    4)
        echo -e "${YELLOW}Enter custom cron schedule (e.g., '0 9 * * 1' for Mondays at 9 AM):${NC}"
        read -p "Cron schedule: " CRON_SCHEDULE
        SCHEDULE_NAME="Custom"
        ;;
    *)
        CRON_SCHEDULE="0 9 * * 1"
        SCHEDULE_NAME="Weekly (Mondays at 9 AM)"
        ;;
esac

# Add to crontab
CRON_JOB="$CRON_SCHEDULE $CRON_SCRIPT"

echo -e "\n${BLUE}📋 Cron Job Summary${NC}"
echo "=================="
echo -e "Repository: ${GREEN}$REPO${NC}"
echo -e "Time Range: ${GREEN}$TIME_RANGE${NC}"
echo -e "Branches: ${GREEN}$BRANCHES${NC}"
echo -e "Schedule: ${GREEN}$SCHEDULE_NAME${NC}"
echo -e "Cron Job: ${YELLOW}$CRON_JOB${NC}"

echo -e "\n${YELLOW}⚠️  Before adding to crontab, please:${NC}"
echo "1. Edit $ENV_FILE and add your actual tokens"
echo "2. Test the script manually first"
echo "3. Ensure all dependencies are installed"

read -p "Add to crontab now? (y/N): " ADD_CRON

if [[ $ADD_CRON =~ ^[Yy]$ ]]; then
    # Check if cron job already exists
    if crontab -l 2>/dev/null | grep -q "$CRON_SCRIPT"; then
        echo -e "${YELLOW}⚠️  Cron job already exists. Updating...${NC}"
        (crontab -l 2>/dev/null | grep -v "$CRON_SCRIPT"; echo "$CRON_JOB") | crontab -
    else
        (crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -
    fi
    
    echo -e "${GREEN}✅ Cron job added successfully!${NC}"
    echo -e "${BLUE}📋 Current crontab:${NC}"
    crontab -l
else
    echo -e "${YELLOW}📝 To add manually later, run:${NC}"
    echo "crontab -e"
    echo "Then add: $CRON_JOB"
fi

echo -e "\n${GREEN}🎉 Setup complete!${NC}"
echo -e "${BLUE}📁 Files created:${NC}"
echo "  - $ENV_FILE (environment variables)"
echo "  - $CRON_SCRIPT (execution script)"
echo "  - $SCRIPT_DIR/slack_reports.log (log file)"
echo ""
echo -e "${YELLOW}🔧 Next steps:${NC}"
echo "1. Edit $ENV_FILE with your actual tokens"
echo "2. Test: python slack_pr_reporter.py $REPO --time-range $TIME_RANGE"
echo "3. Monitor logs: tail -f $SCRIPT_DIR/slack_reports.log" 