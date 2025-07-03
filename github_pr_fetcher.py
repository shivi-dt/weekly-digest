#!/usr/bin/env python3
"""
GitHub PR Fetcher
Fetches Pull Requests from GitHub repositories with configurable time ranges and branch filtering.
"""

import requests
import json
from datetime import datetime, timedelta, timezone
import argparse
from typing import List, Dict, Any, Optional
import os
import sys

class GitHubPRFetcher:
    def __init__(self, token: Optional[str] = None):
        """
        Initialize the GitHub PR fetcher.
        
        Args:
            token: GitHub personal access token (optional, but recommended for higher rate limits)
        """
        self.token = token or os.getenv('GITHUB_TOKEN')
        self.headers = {
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'GitHub-PR-Fetcher'
        }
        
        if self.token:
            self.headers['Authorization'] = f'token {self.token}'
        else:
            print("⚠️  No GitHub token provided. This may fail for private repositories.")
            print("   Set GITHUB_TOKEN environment variable or use --token argument.")
    
    def check_repo_access(self, repo: str) -> bool:
        """
        Check if we can access the repository.
        
        Args:
            repo: Repository name in format 'owner/repo'
            
        Returns:
            True if accessible, False otherwise
        """
        try:
            response = requests.get(f"https://api.github.com/repos/{repo}", headers=self.headers)
            if response.status_code == 200:
                repo_data = response.json()
                print(f"✅ Repository accessible: {repo_data['name']}")
                print(f"   Private: {repo_data['private']}")
                print(f"   Default branch: {repo_data['default_branch']}")
                return True
            elif response.status_code == 404:
                print(f"❌ Repository not found: {repo}")
                print("   Check the repository name and ensure you have access.")
                return False
            elif response.status_code == 401:
                print(f"❌ Authentication required for repository: {repo}")
                print("   Please provide a GitHub personal access token.")
                return False
            else:
                print(f"❌ Error accessing repository: {response.status_code}")
                print(f"   Response: {response.text}")
                return False
        except Exception as e:
            print(f"❌ Error checking repository access: {e}")
            return False
    
    def get_available_branches(self, repo: str) -> List[str]:
        """
        Get list of available branches in the repository.
        
        Args:
            repo: Repository name in format 'owner/repo'
            
        Returns:
            List of branch names
        """
        all_branches = []
        page = 1
        per_page = 100  # Maximum per page
        
        try:
            while True:
                url = f"https://api.github.com/repos/{repo}/branches"
                params = {
                    'page': page,
                    'per_page': per_page
                }
                
                response = requests.get(url, headers=self.headers, params=params)
                if response.status_code == 200:
                    branches = response.json()
                    
                    if not branches:  # No more branches
                        break
                    
                    all_branches.extend([branch['name'] for branch in branches])
                    
                    # If we got less than per_page branches, we've reached the end
                    if len(branches) < per_page:
                        break
                    
                    page += 1
                else:
                    print(f"❌ Error fetching branches: {response.status_code}")
                    print(f"   Response: {response.text}")
                    break
                    
        except Exception as e:
            print(f"❌ Error fetching branches: {e}")
            return []
        
        return all_branches
    
    def get_time_range(self, time_range: str) -> tuple:
        """
        Get start and end dates based on time range string.
        
        Args:
            time_range: One of '1w', '1m', '6m', '1y', 'custom:start:end', or custom date string
            
        Returns:
            Tuple of (start_date, end_date) as ISO format strings
        """
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
            # Custom format: custom:start_date:end_date or custom:start_date
            try:
                parts = time_range.split(':', 2)
                if len(parts) == 2:
                    # Only start date provided, end date is now
                    start_date = datetime.fromisoformat(parts[1])
                elif len(parts) == 3:
                    # Both start and end dates provided
                    start_date = datetime.fromisoformat(parts[1])
                    end_date = datetime.fromisoformat(parts[2])
                else:
                    raise ValueError("Invalid custom format")
            except (ValueError, IndexError):
                raise ValueError(f"Invalid custom date format. Use 'custom:YYYY-MM-DD' or 'custom:YYYY-MM-DD:YYYY-MM-DD'")
        else:
            # Try to parse as custom date
            try:
                start_date = datetime.fromisoformat(time_range.replace('Z', '+00:00'))
            except ValueError:
                raise ValueError(f"Invalid time range: {time_range}. Use '1w', '1m', '6m', '1y', 'custom:YYYY-MM-DD', 'custom:YYYY-MM-DD:YYYY-MM-DD', or ISO date format.")
        
        return start_date.isoformat(), end_date.isoformat()
    
    def fetch_prs(self, repo: str, base_branches: List[str], time_range: str = '1w') -> List[Dict[str, Any]]:
        """
        Fetch Pull Requests from GitHub repository.
        
        Args:
            repo: Repository name in format 'owner/repo'
            base_branches: List of base branches to filter by (e.g., ['main-v2', 'main-v3'])
            time_range: Time range to fetch PRs from
            
        Returns:
            List of PR data dictionaries
        """
        # First check repository access
        if not self.check_repo_access(repo):
            return []
        
        # Get available branches
        available_branches = self.get_available_branches(repo)
        if not available_branches:
            return []
        
        # Filter branches that exist
        valid_branches = [branch for branch in base_branches if branch in available_branches]
        if not valid_branches:
            print(f"❌ None of the specified branches ({', '.join(base_branches)}) exist in the repository.")
            return []
        
        if len(valid_branches) != len(base_branches):
            missing_branches = set(base_branches) - set(valid_branches)
            print(f"⚠️  Some branches not found: {', '.join(missing_branches)}")
            print(f"   Proceeding with available branches: {', '.join(valid_branches)}")
        
        start_date, end_date = self.get_time_range(time_range)
        
        all_prs = []
        
        for base_branch in valid_branches:
            print(f"Fetching PRs merged to {base_branch}...")
            
            # GitHub API endpoint for PRs
            url = f"https://api.github.com/repos/{repo}/pulls"
            
            params = {
                'state': 'closed',  # Get closed PRs (includes merged)
                'base': base_branch,
                'sort': 'updated',
                'direction': 'desc',
                'per_page': 100  # Maximum per page
            }
            
            page = 1
            while True:
                params['page'] = page
                
                try:
                    response = requests.get(url, headers=self.headers, params=params)
                    response.raise_for_status()
                    
                    prs = response.json()
                    
                    if not prs:
                        break
                    
                    # Filter PRs by merge date within time range
                    for pr in prs:
                        if pr.get('merged_at'):
                            merged_date = datetime.fromisoformat(pr['merged_at'].replace('Z', '+00:00'))
                            start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                            end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                            
                            # Ensure all datetime objects are timezone-aware
                            if merged_date.tzinfo is None:
                                merged_date = merged_date.replace(tzinfo=timezone.utc)
                            if start_dt.tzinfo is None:
                                start_dt = start_dt.replace(tzinfo=timezone.utc)
                            if end_dt.tzinfo is None:
                                end_dt = end_dt.replace(tzinfo=timezone.utc)
                            
                            if start_dt <= merged_date <= end_dt:
                                # Add base branch info to PR data
                                pr['base_branch'] = base_branch
                                all_prs.append(pr)
                    
                    # If we got less than 100 PRs, we've reached the end
                    if len(prs) < 100:
                        break
                    
                    page += 1
                    
                except requests.exceptions.RequestException as e:
                    print(f"Error fetching PRs for {base_branch}: {e}")
                    break
        
        # Sort by merge date (newest first)
        all_prs.sort(key=lambda x: x.get('merged_at', ''), reverse=True)
        
        return all_prs
    
    def format_pr_data(self, pr: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format PR data for better readability.
        
        Args:
            pr: Raw PR data from GitHub API
            
        Returns:
            Formatted PR data
        """
        return {
            'number': pr['number'],
            'title': pr['title'],
            'author': pr['user']['login'],
            'base_branch': pr.get('base_branch', pr['base']['ref']),
            'merged_at': pr.get('merged_at'),
            'created_at': pr['created_at'],
            'updated_at': pr['updated_at'],
            'url': pr['html_url'],
            'body': pr.get('body', ''),
            'labels': [label['name'] for label in pr.get('labels', [])],
            'assignees': [assignee['login'] for assignee in pr.get('assignees', [])],
            'reviewers': [reviewer['login'] for reviewer in pr.get('requested_reviewers', [])],
            'commits_count': pr.get('commits', 0),
            'additions': pr.get('additions', 0),
            'deletions': pr.get('deletions', 0),
            'changed_files': pr.get('changed_files', 0)
        }
    
    def save_to_file(self, prs: List[Dict[str, Any]], filename: str):
        """
        Save PR data to JSON file.
        
        Args:
            prs: List of PR data
            filename: Output filename
        """
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(prs, f, indent=2, ensure_ascii=False)
        print(f"Saved {len(prs)} PRs to {filename}")
    
    def print_summary(self, prs: List[Dict[str, Any]]):
        """
        Print a summary of fetched PRs.
        
        Args:
            prs: List of PR data
        """
        if not prs:
            print("No PRs found in the specified time range.")
            return
        
        print(f"\n=== PR Summary ===")
        print(f"Total PRs: {len(prs)}")
        
        # Group by base branch
        by_branch = {}
        for pr in prs:
            branch = pr.get('base_branch', 'unknown')
            if branch not in by_branch:
                by_branch[branch] = []
            by_branch[branch].append(pr)
        
        for branch, branch_prs in by_branch.items():
            print(f"\n{branch}: {len(branch_prs)} PRs")
            for pr in branch_prs[:5]:  # Show first 5 PRs per branch
                print(f"  #{pr['number']}: {pr['title']} (by {pr['author']})")
            if len(branch_prs) > 5:
                print(f"  ... and {len(branch_prs) - 5} more")

    def get_user_time_range(self) -> str:
        """
        Interactive function to get time range from user.
        
        Returns:
            Time range string
        """
        print("\n=== Time Range Selection ===")
        print("1. Last week (1w)")
        print("2. Last month (1m)")
        print("3. Last 6 months (6m)")
        print("4. Last year (1y)")
        print("5. Custom start date (until now)")
        print("6. Custom start and end dates")
        
        while True:
            choice = input("\nEnter your choice (1-6): ").strip()
            
            if choice == '1':
                return '1w'
            elif choice == '2':
                return '1m'
            elif choice == '3':
                return '6m'
            elif choice == '4':
                return '1y'
            elif choice == '5':
                start_date = input("Enter start date (YYYY-MM-DD): ").strip()
                try:
                    datetime.fromisoformat(start_date)
                    return f"custom:{start_date}"
                except ValueError:
                    print("❌ Invalid date format. Please use YYYY-MM-DD")
                    continue
            elif choice == '6':
                print("\nEnter custom date range:")
                start_date = input("Start date (YYYY-MM-DD): ").strip()
                end_date = input("End date (YYYY-MM-DD): ").strip()
                
                try:
                    # Validate dates
                    datetime.fromisoformat(start_date)
                    datetime.fromisoformat(end_date)
                    return f"custom:{start_date}:{end_date}"
                except ValueError:
                    print("❌ Invalid date format. Please use YYYY-MM-DD")
                    continue
            else:
                print("❌ Invalid choice. Please enter 1-6.")


def main():
    parser = argparse.ArgumentParser(description='Fetch Pull Requests from GitHub')
    parser.add_argument('repo', help='Repository name (e.g., DrivetrainAi/drive)')
    parser.add_argument('--branches', nargs='+', default=['main-v2', 'main-v3'], 
                       help='Base branches to filter by (default: main-v2 main-v3)')
    parser.add_argument('--time-range', default='1w', 
                       choices=['1w', '1m', '6m', '1y'],
                       help='Time range to fetch PRs from (default: 1w)')
    parser.add_argument('--output', help='Output JSON file (optional)')
    parser.add_argument('--token', help='GitHub personal access token (optional)')
    parser.add_argument('--check-only', action='store_true', 
                       help='Only check repository access and available branches')
    parser.add_argument('--interactive', action='store_true',
                       help='Interactive mode - ask user for time range')
    
    args = parser.parse_args()
    
    # Initialize fetcher
    fetcher = GitHubPRFetcher(token=args.token)
    
    if args.check_only:
        # Just check repository access and branches
        if fetcher.check_repo_access(args.repo):
            branches = fetcher.get_available_branches(args.repo)
            if branches:
                print(f"\nAvailable branches: {', '.join(branches)}")
        return
    
    # Handle interactive mode
    time_range = args.time_range
    if args.interactive:
        time_range = fetcher.get_user_time_range()
        print(f"\nSelected time range: {time_range}")
    
    # Fetch PRs
    print(f"Fetching PRs from {args.repo} merged to {', '.join(args.branches)} in the last {time_range}...")
    
    prs = fetcher.fetch_prs(args.repo, args.branches, time_range)
    
    # Format PR data
    formatted_prs = [fetcher.format_pr_data(pr) for pr in prs]
    
    # Print summary
    fetcher.print_summary(formatted_prs)
    
    # Save to file if requested
    if args.output:
        fetcher.save_to_file(formatted_prs, args.output)
    else:
        # Save with default filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        default_filename = f"prs_{args.repo.replace('/', '_')}_{time_range}_{timestamp}.json"
        fetcher.save_to_file(formatted_prs, default_filename)


if __name__ == '__main__':
    main() 