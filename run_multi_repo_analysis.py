#!/usr/bin/env python3
"""
Multi-repository GitHub PR Analyzer Wrapper
Runs the github_pr_analyzer.py script for multiple repositories.
"""

import subprocess
import sys
import os
import argparse

def run_analyzer_for_repo(repo, additional_args=None):
    """Run the github_pr_analyzer.py script for a single repository."""
    cmd = [sys.executable, 'github_pr_analyzer.py', repo]
    
    if additional_args:
        cmd.extend(additional_args)
    
    print(f"\n{'='*60}")
    print(f"🚀 Analyzing repository: {repo}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(cmd, check=True)
        print(f"✅ Successfully analyzed {repo}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to analyze {repo}: {e}")
        return False

def main():
    """Main function to run analysis for multiple repositories."""
    parser = argparse.ArgumentParser(
        description='Multi-repository GitHub PR Analyzer Wrapper',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze multiple repositories with default settings
  python run_multi_repo_analysis.py DrivetrainAi/drive DrivetrainAi/tesseract DrivetrainAi/drive-frontend

  # Analyze with custom branches
  python run_multi_repo_analysis.py DrivetrainAi/drive DrivetrainAi/tesseract --branches main develop

  # Analyze with custom time range and send to Slack
  python run_multi_repo_analysis.py DrivetrainAi/drive --time-range 1m --send-to-slack

  # Analyze with all custom options
  python run_multi_repo_analysis.py DrivetrainAi/drive DrivetrainAi/tesseract --branches main-v3 develop --time-range 1w --send-to-slack --output custom_summary.md
        """
    )
    
    # Positional argument for repositories (can be multiple)
    parser.add_argument('repos', nargs='+', 
                       help='Repository names (e.g., DrivetrainAi/drive DrivetrainAi/tesseract)')
    
    # Optional arguments that will be passed to the analyzer
    parser.add_argument('--branches', nargs='+', default=['main-v3'],
                       help='Branches to analyze (default: main-v3)')
    parser.add_argument('--time-range', default='1w',
                       help='Time range (1w, 1m, 6m, 1y, custom:YYYY-MM-DD) (default: 1w)')
    parser.add_argument('--output', 
                       help='Output markdown file (will append repo name if multiple repos)')
    parser.add_argument('--github-token', 
                       help='GitHub token')
    parser.add_argument('--openai-key', 
                       help='OpenAI API key')
    parser.add_argument('--linear-token', 
                       help='Linear API key')
    parser.add_argument('--slack-bot-token', 
                       help='Slack bot token')
    parser.add_argument('--slack-channel-id', 
                       help='Slack channel ID')
    parser.add_argument('--send-to-slack', action='store_true', 
                       help='Send summary to Slack')
    parser.add_argument('--interactive', action='store_true', 
                       help='Interactive mode')
    parser.add_argument('--no-save-raw-data', action='store_false', dest='save_raw_data',
                       help='Disable saving raw GitHub data to JSON file')
    
    args = parser.parse_args()
    
    print("🔍 Multi-Repository GitHub PR Analyzer")
    print(f"📋 Analyzing {len(args.repos)} repositories:")
    for repo in args.repos:
        print(f"   - {repo}")
    print(f"🌿 Branches: {', '.join(args.branches)}")
    print(f"📅 Time range: {args.time_range}")
    
    # Build additional arguments list
    additional_args = []
    
    # Add branches
    if args.branches:
        additional_args.extend(['--branches'] + args.branches)
    
    # Add time range
    if args.time_range:
        additional_args.extend(['--time-range', args.time_range])
    
    # Add output file (modify for multiple repos)
    if args.output:
        if len(args.repos) == 1:
            additional_args.extend(['--output', args.output])
        else:
            # For multiple repos, we'll modify the output name per repo
            pass
    
    # Add other optional arguments
    if args.github_token:
        additional_args.extend(['--github-token', args.github_token])
    if args.openai_key:
        additional_args.extend(['--openai-key', args.openai_key])
    if args.linear_token:
        additional_args.extend(['--linear-token', args.linear_token])
    if args.slack_bot_token:
        additional_args.extend(['--slack-bot-token', args.slack_bot_token])
    if args.slack_channel_id:
        additional_args.extend(['--slack-channel-id', args.slack_channel_id])
    if args.send_to_slack:
        additional_args.append('--send-to-slack')
    if args.interactive:
        additional_args.append('--interactive')
    if not args.save_raw_data:
        additional_args.append('--no-save-raw-data')
    
    success_count = 0
    total_count = len(args.repos)
    
    for i, repo in enumerate(args.repos):
        # Handle output file for multiple repositories
        repo_additional_args = additional_args.copy()
        if args.output and len(args.repos) > 1:
            # Create unique output filename for each repo
            base_name, ext = os.path.splitext(args.output)
            repo_name = repo.replace('/', '_')
            repo_output = f"{base_name}_{repo_name}{ext}"
            # Replace or add output argument
            if '--output' in repo_additional_args:
                output_index = repo_additional_args.index('--output')
                repo_additional_args[output_index + 1] = repo_output
            else:
                repo_additional_args.extend(['--output', repo_output])
        
        if run_analyzer_for_repo(repo, repo_additional_args):
            success_count += 1
    
    print(f"\n{'='*60}")
    print(f"📊 Analysis Complete!")
    print(f"✅ Successful: {success_count}/{total_count}")
    print(f"❌ Failed: {total_count - success_count}/{total_count}")
    print(f"{'='*60}")
    
    if success_count < total_count:
        sys.exit(1)

if __name__ == '__main__':
    main() 