#!/usr/bin/env python3
"""
GitHub PR Analyzer - E2E Solution
Fetches PRs and generates beautiful markdown summaries in one command.
"""

import requests
import json
import argparse
import os
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional
import openai
from openai import OpenAI

class GitHubPRAnalyzer:
    def __init__(self, github_token: Optional[str] = None, openai_key: Optional[str] = None):
        """
        Initialize the analyzer with GitHub and OpenAI credentials.
        """
        self.github_token = github_token or os.getenv('GITHUB_TOKEN')
        self.openai_key = openai_key or os.getenv('OPENAI_API_KEY')
        
        # GitHub setup
        self.github_headers = {
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'GitHub-PR-Analyzer'
        }
        if self.github_token:
            self.github_headers['Authorization'] = f'token {self.github_token}'
        
        # OpenAI setup
        if self.openai_key:
            self.openai_client = OpenAI(api_key=self.openai_key)
        else:
            self.openai_client = None
    
    def get_time_range(self, time_range: str) -> tuple:
        """Get start and end dates based on time range string."""
        end_date = datetime.now()
        
        if time_range == '1w':
            start_date = end_date - timedelta(weeks=1)
        elif time_range == '1m':
            start_date = end_date - timedelta(days=30)
        elif time_range == '6m':
            start_date = end_date - timedelta(days=180)
        elif time_range == '1y':
            start_date = end_date - timedelta(days=365)
        elif time_range.startswith('custom:'):
            try:
                parts = time_range.split(':', 2)
                if len(parts) == 2:
                    start_date = datetime.fromisoformat(parts[1])
                elif len(parts) == 3:
                    start_date = datetime.fromisoformat(parts[1])
                    end_date = datetime.fromisoformat(parts[2])
                else:
                    raise ValueError("Invalid custom format")
            except (ValueError, IndexError):
                raise ValueError(f"Invalid custom date format. Use 'custom:YYYY-MM-DD' or 'custom:YYYY-MM-DD:YYYY-MM-DD'")
        else:
            try:
                start_date = datetime.fromisoformat(time_range.replace('Z', '+00:00'))
            except ValueError:
                raise ValueError(f"Invalid time range: {time_range}")
        
        return start_date.isoformat(), end_date.isoformat()
    
    def fetch_prs(self, repo: str, branches: List[str], time_range: str) -> List[Dict[str, Any]]:
        """Fetch PRs from GitHub repository."""
        start_date, end_date = self.get_time_range(time_range)
        
        all_prs = []
        
        for branch in branches:
            print(f"📥 Fetching PRs from {branch}...")
            
            url = f"https://api.github.com/repos/{repo}/pulls"
            params = {
                'state': 'closed',
                'base': branch,
                'sort': 'updated',
                'direction': 'desc',
                'per_page': 100
            }
            
            page = 1
            while True:
                params['page'] = page
                
                try:
                    response = requests.get(url, headers=self.github_headers, params=params)
                    
                    if response.status_code == 404:
                        print(f"❌ Branch '{branch}' not found or no access. Check if:")
                        print(f"   - Branch exists in the repository")
                        print(f"   - You have access to the repository")
                        print(f"   - GitHub token is set (for private repos)")
                        break
                    elif response.status_code == 401:
                        print(f"❌ Authentication required. Please set GITHUB_TOKEN environment variable.")
                        break
                    elif response.status_code != 200:
                        print(f"❌ Error {response.status_code}: {response.text}")
                        break
                    
                    prs = response.json()
                    if not prs:
                        break
                    
                    # Filter by merge date
                    for pr in prs:
                        if pr.get('merged_at'):
                            merged_date = datetime.fromisoformat(pr['merged_at'].replace('Z', '+00:00'))
                            start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                            end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                            
                            if merged_date.tzinfo is None:
                                merged_date = merged_date.replace(tzinfo=timezone.utc)
                            if start_dt.tzinfo is None:
                                start_dt = start_dt.replace(tzinfo=timezone.utc)
                            if end_dt.tzinfo is None:
                                end_dt = end_dt.replace(tzinfo=timezone.utc)
                            
                            if start_dt <= merged_date <= end_dt:
                                pr['base_branch'] = branch
                                all_prs.append(pr)
                    
                    if len(prs) < 100:
                        break
                    page += 1
                    
                except requests.exceptions.RequestException as e:
                    print(f"❌ Error fetching PRs for {branch}: {e}")
                    break
        
        all_prs.sort(key=lambda x: x.get('merged_at', ''), reverse=True)
        return all_prs
    
    def format_pr_data(self, pr: Dict[str, Any]) -> Dict[str, Any]:
        """Format PR data for summary."""
        # Handle author field properly
        author = 'unknown'
        if pr.get('user') and isinstance(pr['user'], dict):
            author = pr['user'].get('login', 'unknown')
        
        return {
            'number': pr['number'],
            'title': pr['title'],
            'author': author,
            'base_branch': pr.get('base_branch', pr['base']['ref']),
            'merged_at': pr.get('merged_at'),
            'url': pr['html_url'],
            'body': pr.get('body', ''),
            'labels': [label['name'] for label in pr.get('labels', [])],
            'additions': pr.get('additions', 0),
            'deletions': pr.get('deletions', 0),
            'changed_files': pr.get('changed_files', 0),
            'commits_count': pr.get('commits', 0)
        }
    
    def create_summary_prompt(self, prs: List[Dict[str, Any]], time_range: str) -> str:
        """Create a concise prompt for beautiful summary focused on features, enhancements, and bug fixes."""
        
        # Group by branch
        grouped = {}
        for pr in prs:
            branch = pr.get('base_branch', 'unknown')
            if branch not in grouped:
                grouped[branch] = []
            grouped[branch].append(pr)
        
        prompt = f"""Create a beautiful, concise markdown summary of {len(prs)} Pull Requests merged to production in the last {time_range}.

Structure the summary with these sections:

1. **🚀 New Features** - Brand new functionality added
2. **⚡ Enhancements** - Improvements to existing features
3. **🐛 Bug Fixes** - Issues resolved and problems fixed
4. **🔧 Technical Improvements** - Performance, security, infrastructure changes
5. **👥 Top Contributors** - Top 5 developers with their focus areas
6. **📊 Quick Stats** - Summary statistics

For each PR, categorize it based on:
- **Features**: New functionality, endpoints, capabilities
- **Enhancements**: Improvements to existing features, better UX, optimizations
- **Bug Fixes**: Error fixes, issue resolutions, stability improvements
- **Technical**: Performance, security, infrastructure, code quality

Make it:
- ✨ Beautiful and well-formatted with emojis
- 📝 Concise but informative (focus on business impact)
- 🎯 Business-focused (what users/teams will notice)
- 📊 Easy to read and understand

PR Details:
"""
        
        for branch, branch_prs in grouped.items():
            prompt += f"\n## {branch.upper()} ({len(branch_prs)} PRs)\n"
            for pr in branch_prs[:8]:  # Top 8 per branch for better categorization
                author = pr.get('user', {}).get('login', 'unknown') if isinstance(pr.get('user'), dict) else 'unknown'
                prompt += f"- #{pr['number']}: {pr['title']} (by {author})\n"
            if len(branch_prs) > 8:
                prompt += f"- ... and {len(branch_prs) - 8} more\n"
        
        prompt += """

Analyze the PR titles and descriptions to categorize them properly. Focus on what each change means for users and the business. Create a summary that stakeholders would find valuable for understanding what was deployed.
"""
        return prompt
    
    def generate_beautiful_summary(self, prs: List[Dict[str, Any]], time_range: str) -> str:
        """Generate beautiful markdown summary using LLM."""
        if not prs:
            return "# 📊 No Pull Requests Found\n\nNo PRs were merged in the specified time range."
        
        if not self.openai_client:
            return "# ❌ OpenAI API Key Required\n\nPlease set OPENAI_API_KEY environment variable."
        
        prompt = self.create_summary_prompt(prs, time_range)
        
        try:
            print("🤖 Generating beautiful summary...")
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a technical writer specializing in creating beautiful, concise markdown summaries of software deployments. Focus on categorizing changes into: New Features (🚀), Enhancements (⚡), Bug Fixes (🐛), and Technical Improvements (🔧). Use emojis, clear formatting, and emphasize business value and user impact. Make the summary engaging and easy to understand for stakeholders."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,
                max_tokens=2000
            )
            
            summary = response.choices[0].message.content
            print("✅ Beautiful summary generated!")
            return summary
            
        except Exception as e:
            print(f"❌ Error generating summary: {e}")
            return f"# ❌ Summary Generation Failed\n\nError: {e}"
    
    def save_summary(self, summary: str, output_file: str):
        """Save summary to markdown file."""
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(summary)
            print(f"💾 Summary saved to: {output_file}")
        except Exception as e:
            print(f"❌ Error saving summary: {e}")
    
    def print_summary(self, summary: str):
        """Print summary to console."""
        print("\n" + "🎉" + "="*78 + "🎉")
        print("                    GITHUB PR SUMMARY")
        print("🎉" + "="*78 + "🎉")
        print(summary)
        print("🎉" + "="*78 + "🎉")


def get_user_time_range() -> str:
    """Interactive time range selection."""
    print("\n⏰ Select Time Range:")
    print("1. Last week (1w)")
    print("2. Last month (1m)")
    print("3. Last 6 months (6m)")
    print("4. Last year (1y)")
    print("5. Custom start date (until now)")
    print("6. Custom start and end dates")
    
    while True:
        choice = input("\nEnter choice (1-6): ").strip()
        
        if choice == '1': return '1w'
        elif choice == '2': return '1m'
        elif choice == '3': return '6m'
        elif choice == '4': return '1y'
        elif choice == '5':
            start_date = input("Enter start date (YYYY-MM-DD): ").strip()
            try:
                datetime.fromisoformat(start_date)
                return f"custom:{start_date}"
            except ValueError:
                print("❌ Invalid date format. Use YYYY-MM-DD")
                continue
        elif choice == '6':
            start_date = input("Start date (YYYY-MM-DD): ").strip()
            end_date = input("End date (YYYY-MM-DD): ").strip()
            try:
                datetime.fromisoformat(start_date)
                datetime.fromisoformat(end_date)
                return f"custom:{start_date}:{end_date}"
            except ValueError:
                print("❌ Invalid date format. Use YYYY-MM-DD")
                continue
        else:
            print("❌ Invalid choice. Enter 1-6.")


def main():
    parser = argparse.ArgumentParser(description='GitHub PR Analyzer - E2E Solution')
    parser.add_argument('repo', help='Repository name (e.g., DrivetrainAi/drive)')
    parser.add_argument('--branches', nargs='+', default=['main-v2', 'main-v3'], 
                       help='Branches to analyze (default: main-v2 main-v3)')
    parser.add_argument('--time-range', help='Time range (1w, 1m, 6m, 1y, custom:YYYY-MM-DD)')
    parser.add_argument('--output', help='Output markdown file')
    parser.add_argument('--github-token', help='GitHub token')
    parser.add_argument('--openai-key', help='OpenAI API key')
    parser.add_argument('--interactive', action='store_true', help='Interactive mode')
    
    args = parser.parse_args()
    
    # Initialize analyzer
    analyzer = GitHubPRAnalyzer(
        github_token=args.github_token,
        openai_key=args.openai_key
    )
    
    # Check for required tokens
    if not analyzer.github_token:
        print("❌ GitHub token is required for private repositories.")
        print("   Set GITHUB_TOKEN environment variable or use --github-token")
        print("   Example: export GITHUB_TOKEN=your_token_here")
        return
    
    if not analyzer.openai_key:
        print("❌ OpenAI API key is required for generating summaries.")
        print("   Set OPENAI_API_KEY environment variable or use --openai-key")
        print("   Example: export OPENAI_API_KEY=your_key_here")
        return
    
    # Get time range
    time_range = args.time_range
    if args.interactive or not time_range:
        time_range = get_user_time_range()
    
    print(f"\n🚀 Analyzing PRs from {args.repo}")
    print(f"📅 Time range: {time_range}")
    print(f"🌿 Branches: {', '.join(args.branches)}")
    
    # Fetch PRs
    prs = analyzer.fetch_prs(args.repo, args.branches, time_range)
    
    if not prs:
        print("❌ No PRs found in the specified time range.")
        return
    
    print(f"✅ Found {len(prs)} PRs")
    
    # Generate summary
    summary = analyzer.generate_beautiful_summary(prs, time_range)
    
    # Save to file
    if args.output:
        analyzer.save_summary(summary, args.output)
    else:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        default_filename = f"pr_summary_{timestamp}.md"
        analyzer.save_summary(summary, default_filename)
    
    # Print to console
    analyzer.print_summary(summary)


if __name__ == '__main__':
    main() 