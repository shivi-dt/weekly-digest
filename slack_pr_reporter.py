#!/usr/bin/env python3
"""
Slack PR Reporter
Sends GitHub PR summaries to Slack channels automatically.
"""

import os
import json
import argparse
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional
import requests
from github_pr_analyzer import GitHubPRAnalyzer

class SlackPRReporter:
    def __init__(self, slack_webhook_url: Optional[str] = None, slack_token: Optional[str] = None):
        """
        Initialize the Slack reporter.
        
        Args:
            slack_webhook_url: Slack webhook URL for posting messages
            slack_token: Slack bot token for more advanced features
        """
        self.webhook_url = slack_webhook_url or os.getenv('SLACK_WEBHOOK_URL')
        self.slack_token = slack_token or os.getenv('SLACK_BOT_TOKEN')
        
        if not self.webhook_url and not self.slack_token:
            raise ValueError("Either SLACK_WEBHOOK_URL or SLACK_BOT_TOKEN must be provided")
    
    def format_slack_message(self, summary: str, repo: str, time_range: str, pr_count: int) -> Dict[str, Any]:
        """
        Format the summary for Slack with proper markdown and structure.
        
        Args:
            summary: Generated markdown summary
            repo: Repository name
            time_range: Time range analyzed
            pr_count: Number of PRs analyzed
            
        Returns:
            Slack message payload
        """
        # Convert markdown to Slack format
        slack_text = self.convert_markdown_to_slack(summary)
        
        # Create a beautiful Slack message
        message = {
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": f"🚀 GitHub PR Summary - {repo}",
                        "emoji": True
                    }
                },
                {
                    "type": "context",
                    "elements": [
                        {
                            "type": "mrkdwn",
                            "text": f"📅 Time Period: {time_range} | 📊 Total PRs: {pr_count} | ⏰ Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
                        }
                    ]
                },
                {
                    "type": "divider"
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": slack_text
                    }
                },
                {
                    "type": "divider"
                },
                {
                    "type": "context",
                    "elements": [
                        {
                            "type": "mrkdwn",
                            "text": "🤖 Generated automatically by GitHub PR Analyzer"
                        }
                    ]
                }
            ]
        }
        
        return message
    
    def convert_markdown_to_slack(self, markdown: str) -> str:
        """
        Convert markdown formatting to Slack-compatible formatting.
        
        Args:
            markdown: Markdown text
            
        Returns:
            Slack-formatted text
        """
        # Convert markdown headers to bold
        slack_text = markdown
        
        # Convert headers
        slack_text = slack_text.replace('# ', '*')
        slack_text = slack_text.replace('## ', '*')
        slack_text = slack_text.replace('### ', '*')
        
        # Convert bold
        slack_text = slack_text.replace('**', '*')
        
        # Convert lists
        slack_text = slack_text.replace('- ', '• ')
        
        # Convert code blocks
        slack_text = slack_text.replace('```', '`')
        
        # Handle line breaks for Slack
        slack_text = slack_text.replace('\n\n', '\n')
        
        return slack_text
    
    def send_to_slack(self, message: Dict[str, Any]) -> bool:
        """
        Send message to Slack.
        
        Args:
            message: Slack message payload
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if self.webhook_url:
                # Use webhook for simple posting
                response = requests.post(
                    self.webhook_url,
                    json=message,
                    headers={'Content-Type': 'application/json'}
                )
                response.raise_for_status()
                print("✅ Message sent to Slack via webhook")
                return True
                
            elif self.slack_token:
                # Use bot token for more advanced features
                response = requests.post(
                    'https://slack.com/api/chat.postMessage',
                    json=message,
                    headers={
                        'Authorization': f'Bearer {self.slack_token}',
                        'Content-Type': 'application/json'
                    }
                )
                response.raise_for_status()
                result = response.json()
                
                if result.get('ok'):
                    print("✅ Message sent to Slack via bot token")
                    return True
                else:
                    print(f"❌ Slack API error: {result.get('error')}")
                    return False
                    
        except Exception as e:
            print(f"❌ Error sending to Slack: {e}")
            return False
    
    def send_pr_summary(self, repo: str, time_range: str, branches: List[str] = None) -> bool:
        """
        Generate and send PR summary to Slack.
        
        Args:
            repo: Repository name
            time_range: Time range to analyze
            branches: Branches to analyze
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Initialize analyzer
            analyzer = GitHubPRAnalyzer()
            
            # Check for required tokens
            if not analyzer.github_token:
                print("❌ GitHub token is required")
                return False
            
            if not analyzer.openai_key:
                print("❌ OpenAI API key is required")
                return False
            
            print(f"📊 Generating PR summary for {repo} ({time_range})...")
            
            # Fetch PRs
            branches = branches or ['main-v2', 'main-v3']
            prs = analyzer.fetch_prs(repo, branches, time_range)
            
            if not prs:
                print("❌ No PRs found in the specified time range")
                return False
            
            print(f"✅ Found {len(prs)} PRs")
            
            # Generate summary
            summary = analyzer.generate_beautiful_summary(prs, time_range)
            
            # Format for Slack
            message = self.format_slack_message(summary, repo, time_range, len(prs))
            
            # Send to Slack
            return self.send_to_slack(message)
            
        except Exception as e:
            print(f"❌ Error generating/sending summary: {e}")
            return False


def main():
    parser = argparse.ArgumentParser(description='Send GitHub PR summaries to Slack')
    parser.add_argument('repo', help='Repository name (e.g., DrivetrainAi/drive)')
    parser.add_argument('--time-range', default='1w', 
                       help='Time range (1w, 1m, 6m, 1y, custom:YYYY-MM-DD)')
    parser.add_argument('--branches', nargs='+', default=['main-v2', 'main-v3'],
                       help='Branches to analyze')
    parser.add_argument('--slack-webhook', help='Slack webhook URL')
    parser.add_argument('--slack-token', help='Slack bot token')
    parser.add_argument('--channel', help='Slack channel to post to (with bot token)')
    
    args = parser.parse_args()
    
    try:
        # Initialize reporter
        reporter = SlackPRReporter(
            slack_webhook_url=args.slack_webhook,
            slack_token=args.slack_token
        )
        
        # Send summary
        success = reporter.send_pr_summary(args.repo, args.time_range, args.branches)
        
        if success:
            print("🎉 PR summary sent to Slack successfully!")
        else:
            print("❌ Failed to send PR summary to Slack")
            exit(1)
            
    except Exception as e:
        print(f"❌ Error: {e}")
        exit(1)


if __name__ == '__main__':
    main() 