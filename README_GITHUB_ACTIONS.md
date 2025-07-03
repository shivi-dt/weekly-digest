# GitHub Actions PR Summary Workflow

This GitHub Actions workflow automatically generates PR summaries and sends them to Slack on a schedule.

## 🚀 Features

- **Automated Scheduling**: Runs every Monday at 9 AM UTC
- **Manual Triggering**: Can be triggered manually with custom parameters
- **Slack Integration**: Sends beautiful formatted summaries to Slack
- **Error Handling**: Sends notifications when the workflow fails
- **Artifact Storage**: Saves summaries as downloadable artifacts
- **Flexible Configuration**: Customizable time ranges and branches

## 📋 Prerequisites

1. **GitHub Repository**: This workflow must be in the repository you want to analyze
2. **GitHub Secrets**: Set up the following secrets in your repository settings
3. **Slack App**: Create a Slack app with bot token permissions

## 🔧 Setup Instructions

### 1. Repository Secrets

Go to your GitHub repository → Settings → Secrets and variables → Actions, and add these secrets:

#### Required Secrets:
- `GITHUB_TOKEN` (automatically provided by GitHub)
- `OPENAI_API_KEY`: Your OpenAI API key for generating summaries
- `SLACK_BOT_TOKEN`: Your Slack bot token (starts with `xoxb-`)
- `SLACK_CHANNEL_ID`: The Slack channel ID where summaries will be posted

#### How to get Slack credentials:

1. **Create a Slack App**:
   - Go to [api.slack.com/apps](https://api.slack.com/apps)
   - Click "Create New App" → "From scratch"
   - Name your app (e.g., "GitHub PR Reporter")
   - Select your workspace

2. **Configure Bot Token Scopes**:
   - Go to "OAuth & Permissions"
   - Add these scopes:
     - `chat:write` (to post messages)
     - `chat:write.public` (to post in public channels)
   - Install the app to your workspace
   - Copy the "Bot User OAuth Token" (starts with `xoxb-`)

3. **Get Channel ID**:
   - In Slack, right-click the channel → "Copy link"
   - The channel ID is the last part of the URL (e.g., `C1234567890`)

### 2. Workflow File

The workflow file is already created at `.github/workflows/pr-summary-slack.yml`. It includes:

- **Scheduled runs**: Every Monday at 9 AM UTC
- **Manual triggers**: With customizable time ranges and branches
- **Error handling**: Notifications when things go wrong
- **Artifact storage**: 30-day retention of generated summaries

### 3. Customization Options

#### Time Ranges
- `1w`: Last week
- `1m`: Last month  
- `6m`: Last 6 months
- `1y`: Last year

#### Branches
Default: `main-v2,main-v3`
You can modify this in the workflow file or specify when triggering manually.

## 🎯 Usage

### Automatic Scheduling
The workflow runs automatically every Monday at 9 AM UTC. No action required.

### Manual Triggering
1. Go to your repository on GitHub
2. Click "Actions" tab
3. Select "PR Summary to Slack" workflow
4. Click "Run workflow"
5. Choose your options:
   - **Time range**: 1w, 1m, 6m, 1y
   - **Branches**: Comma-separated list (e.g., `main-v2,main-v3,develop`)

### Custom Schedule
To change the schedule, edit the `cron` expression in the workflow file:

```yaml
on:
  schedule:
    # Current: Every Monday at 9 AM UTC
    - cron: '0 9 * * 1'
    
    # Examples:
    # Daily at 9 AM: '0 9 * * *'
    # Every Friday at 5 PM: '0 17 * * 5'
    # Every 2 weeks on Monday: '0 9 * * 1'
```

## 📊 Output

### Slack Message Format
The workflow sends a beautifully formatted Slack message with:
- Header with repository name
- Time period and PR count
- Generated summary in code block
- Link to the GitHub Actions run

### Artifacts
Each run creates downloadable artifacts:
- `pr_summary.json`: Complete summary data
- `summary.md`: Markdown formatted summary

## 🔍 Monitoring

### View Workflow Runs
1. Go to repository → Actions tab
2. Click on "PR Summary to Slack"
3. View run history and logs

### Check Slack
- Successful runs: Beautiful formatted summary
- Failed runs: Error notification with link to logs

### Logs
- All logs are available in the GitHub Actions run
- Failed runs include detailed error information
- Slack notifications include direct links to logs

## 🛠️ Troubleshooting

### Common Issues

1. **"GitHub token not found"**
   - The `GITHUB_TOKEN` is automatically provided
   - Ensure the workflow has access to the repository

2. **"OpenAI API key not found"**
   - Add your OpenAI API key to repository secrets
   - Ensure the key has sufficient credits

3. **"Slack bot token not found"**
   - Add your Slack bot token to repository secrets
   - Ensure the bot has proper permissions

4. **"Channel not found"**
   - Verify the channel ID is correct
   - Ensure the bot is added to the channel
   - Check bot permissions

5. **"No PRs found"**
   - Verify the time range and branches
   - Check if the repository has PRs in the specified time period

### Debug Mode
To debug issues:
1. Trigger the workflow manually
2. Check the logs in the Actions tab
3. Verify all secrets are set correctly
4. Test the Slack bot permissions

## 🔄 Migration from Cron

If you were using the cron-based solution:

1. **Remove cron jobs**:
   ```bash
   crontab -l | grep -v "slack_pr_reporter" | crontab -
   ```

2. **Delete old files**:
   ```bash
   rm setup_cron.sh slack_pr_reporter.py .env
   ```

3. **Set up GitHub Actions**:
   - Follow the setup instructions above
   - Test with manual trigger
   - Monitor the first scheduled run

## 📈 Benefits of GitHub Actions

- **No server required**: Runs in GitHub's infrastructure
- **Better monitoring**: Built-in logs and run history
- **Easy debugging**: Step-by-step execution logs
- **Version control**: Workflow changes are tracked
- **Team collaboration**: Everyone can see and modify workflows
- **Integration**: Native GitHub integration
- **Reliability**: GitHub's infrastructure is highly available

## 🤝 Contributing

To modify the workflow:
1. Edit `.github/workflows/pr-summary-slack.yml`
2. Test with manual trigger
3. Commit and push changes
4. Monitor the next scheduled run

## 📞 Support

If you encounter issues:
1. Check the GitHub Actions logs
2. Verify all secrets are set correctly
3. Test the Slack bot permissions
4. Review the troubleshooting section above 