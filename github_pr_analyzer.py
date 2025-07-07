#!/usr/bin/env python3
"""
GitHub PR Analyzer with Linear Integration and Slack Support
Generates business-friendly summaries of Pull Requests with Linear issue details.
"""

import requests
import json
import argparse
import os
import sys
import re
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional, Tuple
import openai
from openai import OpenAI

# Constants
DEFAULT_BRANCHES = ['main-v3']
DEFAULT_TIME_RANGE = '1w'
MAX_SLACK_TEXT_LENGTH = 3000
MAX_SLACK_SIMPLE_LENGTH = 40000
SLACK_API_BASE = "https://slack.com/api/chat.postMessage"

# Linear API configuration
LINEAR_API_BASE = "https://api.linear.app/graphql"
LINEAR_QUERY = """
query Issue($id: String!) {
  issue(id: $id) {
    id
    title
    description
    state {
      name
    }
    priority
    labels {
      nodes {
        name
      }
    }
    assignee {
      name
      email
    }
    project {
      name
      description
    }
    team {
      name
      key
    }
    cycle {
      name
      number
    }
    comments {
      nodes {
        body
        user {
          name
        }
      }
    }
  }
}
"""

class GitHubPRAnalyzer:
    """Main analyzer class for GitHub PRs with Linear integration."""
    
    def __init__(self, github_token: Optional[str] = None, openai_key: Optional[str] = None, 
                 linear_token: Optional[str] = None, save_raw_data: bool = True):
        """Initialize the analyzer with all required tokens."""
        self.github_token = github_token or os.getenv('GITHUB_TOKEN')
        self.openai_key = openai_key or os.getenv('OPENAI_API_KEY')
        self.linear_token = linear_token or os.getenv('LINEAR_API_KEY')
        self.save_raw_data = save_raw_data
        
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
        
        # Linear setup
        if self.linear_token:
            self.linear_headers = {
                'Authorization': self.linear_token,
                'Content-Type': 'application/json'
            }
        else:
            self.linear_headers = None
    
    def get_time_range(self, time_range: str) -> Tuple[str, str]:
        """Get start and end dates based on time range string. For 1w, use the 7 days before today (not including today). For all other ranges, end_date is yesterday."""
        now = datetime.now(timezone.utc)
        today = now.date()
        yesterday = today - timedelta(days=1)
        if time_range == '1w':
            end_date = yesterday
            start_date = end_date - timedelta(days=6)
            start_date = datetime.combine(start_date, datetime.min.time(), tzinfo=timezone.utc)
            end_date = datetime.combine(end_date, datetime.max.time(), tzinfo=timezone.utc)
        elif time_range == '1m':
            end_date = yesterday
            start_date = end_date - timedelta(days=29)
            start_date = datetime.combine(start_date, datetime.min.time(), tzinfo=timezone.utc)
            end_date = datetime.combine(end_date, datetime.max.time(), tzinfo=timezone.utc)
        elif time_range == '6m':
            end_date = yesterday
            start_date = end_date - timedelta(days=179)
            start_date = datetime.combine(start_date, datetime.min.time(), tzinfo=timezone.utc)
            end_date = datetime.combine(end_date, datetime.max.time(), tzinfo=timezone.utc)
        elif time_range == '1y':
            end_date = yesterday
            start_date = end_date - timedelta(days=364)
            start_date = datetime.combine(start_date, datetime.min.time(), tzinfo=timezone.utc)
            end_date = datetime.combine(end_date, datetime.max.time(), tzinfo=timezone.utc)
        elif time_range.startswith('custom:'):
            start_date, custom_end_date = self._parse_custom_time_range(time_range)
            now_dt = datetime.combine(yesterday, datetime.max.time(), tzinfo=timezone.utc)
            # If custom end date is in the future, use yesterday instead
            if custom_end_date > now_dt:
                end_date = now_dt
            else:
                end_date = custom_end_date
        else:
            end_date = yesterday
            start_date = end_date - timedelta(weeks=1)
            start_date = datetime.combine(start_date, datetime.min.time(), tzinfo=timezone.utc)
            end_date = datetime.combine(end_date, datetime.max.time(), tzinfo=timezone.utc)
        return start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')
    
    def _parse_custom_time_range(self, time_range: str) -> Tuple[datetime, datetime]:
        """Parse custom time range format."""
        parts = time_range.split(':')
        if len(parts) == 2:
            # custom:start_date
            start_date = self._parse_iso_date(parts[1])
            end_date = datetime.now(timezone.utc)
        elif len(parts) == 3:
            # custom:start_date:end_date
            start_date = self._parse_iso_date(parts[1])
            end_date = self._parse_iso_date(parts[2])
        else:
            raise ValueError("Invalid custom time range format")
        
        return start_date, end_date
    
    def _parse_iso_date(self, date_str: str) -> datetime:
        """Parse ISO date string to datetime."""
        return datetime.fromisoformat(date_str).replace(tzinfo=timezone.utc)
    
    def fetch_prs(self, repo: str, branches: List[str], time_range: str) -> List[Dict[str, Any]]:
        """Fetch PRs from specified branches within time range."""
        start_date, end_date = self.get_time_range(time_range)
        print(f"📅 Fetching PRs from {start_date} to {end_date}")
        
        all_prs = []
        linear_enabled = bool(self.linear_token)
        
        for branch in branches:
            print(f"🌿 Fetching PRs from {branch}...")
            branch_prs = self._fetch_branch_prs(repo, branch, start_date, end_date)
            all_prs.extend(branch_prs)
        
        # Remove duplicates and sort by merge date
        unique_prs = {}
        for pr in all_prs:
            pr_id = pr['number']
            if pr_id not in unique_prs:
                unique_prs[pr_id] = pr
        
        all_prs = list(unique_prs.values())
        all_prs.sort(key=lambda x: x.get('merged_at', ''), reverse=True)
        
        print(f"✅ Found {len(all_prs)} PRs")
        
        # Save raw data if enabled
        if self.save_raw_data:
            self._save_raw_data(all_prs, repo, time_range, start_date, end_date)
        
        # Extract Linear IDs and fetch details
        if linear_enabled:
            linear_prs = [pr for pr in all_prs if self._extract_linear_id(pr)]
            print(f"🔗 Linear integration enabled - found {len(linear_prs)} PRs with Linear IDs")
            
            for pr in linear_prs:
                linear_id = self._extract_linear_id(pr)
                if linear_id:
                    print(f"🔗 Found Linear ID in PR #{pr['number']}: {linear_id}")
                    linear_details = self._fetch_linear_details(linear_id)
                    if linear_details:
                        print(f"📋 Fetched Linear details for {linear_id}: {linear_details.get('title', '')[:50]}...")
                        pr['linear_details'] = linear_details
        
        return all_prs
    
    def _fetch_branch_prs(self, repo: str, branch: str, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """Fetch PRs for a specific branch."""
        prs = []
        page = 1
        per_page = 100
        
        while True:
            try:
                url = f"https://api.github.com/repos/{repo}/pulls"
                params = {
                    'state': 'closed',
                    'base': branch,
                    'sort': 'updated',
                    'direction': 'desc',
                    'per_page': per_page,
                    'page': page
                }
                
                response = requests.get(url, headers=self.github_headers, params=params)
                response.raise_for_status()
                
                page_prs = response.json()
                if not page_prs:
                    break
                
                # Filter by merge date and add branch info
                for pr in page_prs:
                    if pr.get('merged_at'):
                        merged_date = datetime.fromisoformat(pr['merged_at'].replace('Z', '+00:00'))
                        start_dt = datetime.fromisoformat(start_date).replace(tzinfo=timezone.utc)
                        end_dt = datetime.fromisoformat(end_date).replace(tzinfo=timezone.utc)
                        
                        if start_dt <= merged_date <= end_dt:
                            pr['base_branch'] = branch
                            prs.append(pr)
                
                if len(page_prs) < per_page:
                    break
                page += 1
                
            except requests.exceptions.RequestException as e:
                print(f"❌ Error fetching PRs for {branch}: {e}")
                break
        
        return prs
    
    def _filter_prs_by_date(self, prs: List[Dict[str, Any]], start_date: str, end_date: str, branch: str) -> List[Dict[str, Any]]:
        """Filter PRs by merge date and add branch info."""
        filtered_prs = []
        start_dt = datetime.fromisoformat(start_date).replace(tzinfo=timezone.utc)
        end_dt = datetime.fromisoformat(end_date).replace(tzinfo=timezone.utc)
        
        for pr in prs:
            if pr.get('merged_at'):
                merged_date = datetime.fromisoformat(pr['merged_at'].replace('Z', '+00:00'))
                if start_dt <= merged_date <= end_dt:
                    pr['base_branch'] = branch
                    filtered_prs.append(pr)
        
        return filtered_prs

    def _extract_linear_id(self, pr: Dict[str, Any]) -> Optional[str]:
        """Extract Linear ID from PR title or body."""
        # Check PR title
        title = pr.get('title', '') or ''
        linear_match = re.search(r'([A-Z]+-\d+)', title)
        if linear_match:
            return linear_match.group(1)
        
        # Check PR body
        body = pr.get('body', '') or ''
        linear_match = re.search(r'([A-Z]+-\d+)', body)
        if linear_match:
            return linear_match.group(1)
        
        # Check commit messages
        commits_url = pr.get('commits_url', '')
        if commits_url and self.github_token:
            try:
                response = requests.get(commits_url, headers=self.github_headers)
                if response.status_code == 200:
                    commits = response.json()
                    for commit in commits:
                        commit_message = commit.get('commit', {}).get('message', '') or ''
                        linear_match = re.search(r'([A-Z]+-\d+)', commit_message)
                        if linear_match:
                            return linear_match.group(1)
            except:
                pass
        
        return None
    
    def _fetch_linear_details(self, linear_id: str) -> Optional[Dict[str, Any]]:
        """Fetch Linear details for a given Linear ID."""
        if not self.linear_headers:
            return None
        
        try:
            payload = {
                "query": LINEAR_QUERY,
                "variables": {"id": linear_id}
            }
            
            response = requests.post(LINEAR_API_BASE, headers=self.linear_headers, json=payload)
            response.raise_for_status()
            
            data = response.json()
            if 'data' in data and data['data'] and data['data'].get('issue'):
                return data['data']['issue']
            
        except Exception as e:
            print(f"❌ Error fetching Linear details for {linear_id}: {e}")
        
        return None
    
    def _extract_linear_business_insights(self, prs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract business insights from Linear data."""
        insights = {
            'total_linear_items': 0,
            'high_priority_items': [],
            'priority_distribution': {},
            'label_distribution': {},
            'team_distribution': {},
            'project_distribution': {}
        }
        
        for pr in prs:
            linear_details = pr.get('linear_details')
            if not linear_details:
                continue
            
            insights['total_linear_items'] += 1
            
            # Priority analysis
            priority = linear_details.get('priority', '') or ''
            if priority:
                insights['priority_distribution'][priority] = insights['priority_distribution'].get(priority, 0) + 1
                if priority in ['Urgent', 'High']:
                    insights['high_priority_items'].append({
                        'id': linear_details.get('id'),
                        'title': linear_details.get('title', '') or '',
                        'priority': priority
                    })
            
            # Label analysis
            labels = linear_details.get('labels', {}) or {}
            if labels and isinstance(labels, dict):
                label_nodes = labels.get('nodes', []) or []
                for label in label_nodes:
                    if label and isinstance(label, dict):
                        label_name = label.get('name', '') or ''
                        if label_name:
                            insights['label_distribution'][label_name] = insights['label_distribution'].get(label_name, 0) + 1
            
            # Team analysis
            team = linear_details.get('team', {}) or {}
            if team and isinstance(team, dict):
                team_name = team.get('name', '') or ''
                if team_name:
                    insights['team_distribution'][team_name] = insights['team_distribution'].get(team_name, 0) + 1
            
            # Project analysis
            project = linear_details.get('project', {}) or {}
            if project and isinstance(project, dict):
                project_name = project.get('name', '') or ''
                if project_name:
                    insights['project_distribution'][project_name] = insights['project_distribution'].get(project_name, 0) + 1
        
        return insights

    def _save_raw_data(self, prs: List[Dict[str, Any]], repo: str, time_range: str, start_date: str, end_date: str) -> None:
        """Save raw GitHub data to JSON file."""
        try:
            # Create metadata
            metadata = {
                "repository": repo,
                "time_range": time_range,
                "start_date": start_date,
                "end_date": end_date,
                "fetch_timestamp": datetime.now().isoformat(),
                "total_prs": len(prs),
                "branches_analyzed": list(set(pr.get('base_branch', 'unknown') for pr in prs)),
                "statistics": self._extract_statistics(prs)
            }
            
            # Create complete data structure
            raw_data = {
                "metadata": metadata,
                "pull_requests": prs
            }
            
            # Generate filename with timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"raw_github_data_{repo.replace('/', '_')}_{time_range}_{timestamp}.json"
            
            # Save to file
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(raw_data, f, indent=2, ensure_ascii=False, default=str)
            
            print(f"💾 Raw GitHub data saved to: {filename}")
            
        except Exception as e:
            print(f"⚠️ Warning: Failed to save raw data: {e}")
    
    def _extract_statistics(self, prs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract useful statistics from PR data."""
        if not prs:
            return {}
        
        # Author statistics
        authors = {}
        total_additions = 0
        total_deletions = 0
        total_changed_files = 0
        total_commits = 0
        
        for pr in prs:
            author = self._get_pr_author(pr)
            if author not in authors:
                authors[author] = {
                    'pr_count': 0,
                    'additions': 0,
                    'deletions': 0,
                    'changed_files': 0,
                    'commits': 0
                }
            
            authors[author]['pr_count'] += 1
            authors[author]['additions'] += pr.get('additions', 0)
            authors[author]['deletions'] += pr.get('deletions', 0)
            authors[author]['changed_files'] += pr.get('changed_files', 0)
            authors[author]['commits'] += pr.get('commits', 0)
            
            total_additions += pr.get('additions', 0)
            total_deletions += pr.get('deletions', 0)
            total_changed_files += pr.get('changed_files', 0)
            total_commits += pr.get('commits', 0)
        
        # Sort authors by PR count
        sorted_authors = sorted(authors.items(), key=lambda x: x[1]['pr_count'], reverse=True)
        
        return {
            'total_prs': len(prs),
            'total_additions': total_additions,
            'total_deletions': total_deletions,
            'total_changed_files': total_changed_files,
            'total_commits': total_commits,
            'unique_authors': len(authors),
            'top_authors': sorted_authors[:5],  # Top 5 authors
            'average_pr_size': {
                'additions': total_additions // len(prs) if prs else 0,
                'deletions': total_deletions // len(prs) if prs else 0,
                'changed_files': total_changed_files // len(prs) if prs else 0,
                'commits': total_commits // len(prs) if prs else 0
            }
        }
    
    def _format_summary_with_links(self, summary: str, prs: List[Dict[str, Any]], repo: str) -> str:
        """Format summary so that only the PR number is a clickable link (e.g., #3666)."""
        # Replace all #<number> with Slack links
        def pr_link_replacer(match):
            pr_num = match.group(1)
            return f"<https://github.com/{repo}/pull/{pr_num}|#{pr_num}>"
        
        formatted_summary = re.sub(r'#(\d+)', pr_link_replacer, summary)
        return formatted_summary

    def create_summary_prompt(self, prs: List[Dict[str, Any]], time_range: str) -> str:
        """Create an exciting weekly digest prompt."""
        
        # Group by branch
        grouped = {}
        for pr in prs:
            branch = pr.get('base_branch', 'unknown')
            if branch not in grouped:
                grouped[branch] = []
            grouped[branch].append(pr)
        
        prompt = f"""Create an exciting weekly digest of {len(prs)} Pull Requests that shipped to production!

This is our weekly development roundup - make it engaging and fun to read while highlighting the impact.

Structure the digest with these exciting sections with these headings in Bold Letters:

1. ## This Week's Highlights - In 1-2 short, specific sentences, no. of prs merged,summarize the most important concrete achievements. Do not use emojis or generic praise.
2. ## 🚀 What's New - Fresh features that users will love (1-2 items max)
3. ## ⚡ Level Up - Cool improvements that make things better (2-3 items max)
4. ## 🐛 Bug Squashed - Issues we conquered (2-3 items max)
5. ## 🔧 Behind the Scenes - Technical wins that keep things running smoothly (1-2 items max)

Make it:
- 🎉 Exciting and celebratory tone with technical precision
- 📝 Concise but impactful (under 250 words)
- 🎯 Focus on user benefits, business wins, and technical achievements
- 💪 Use action words, positive language, and technical terminology
- 🏆 Highlight achievements, performance improvements, and system enhancements
- 📏 Add a blank line between each section for better readability
- 🔬 Include relevant technical details (APIs, databases, performance metrics, etc.)
- 📊 Mention specific improvements (latency reduction, throughput increase, etc.)
- 🛡️ Reference security, scalability, or reliability improvements where applicable
- Do not use emojis or generic praise in the Highlights section. Be specific and concrete.
- Do not include a summary line with PR numbers or links at the end of the digest.

Think of this as a weekly newsletter that gets the team pumped about what we built!

Technical Enhancement Tips:
- Mention specific performance improvements if any.(e.g., "reduced API response time by 40%")
- Reference database optimizations, caching improvements, or scalability enhancements if any.
- Include security updates, authentication improvements, or compliance changes if any.
- Highlight API versioning, endpoint additions, or integration improvements if any.
- Mention monitoring, logging, or observability enhancements if any.
- Reference infrastructure improvements, deployment optimizations, or CI/CD changes if any.
- Dont provide false information.


Analyze the PR titles, CodeRabbit comments in PRs, descriptions, Linear issues linked to them to categorize them properly. Focus on what each change means for users and the business. Create an exciting digest that celebrates our team's achievements!
"""
        return prompt
    
    def _group_prs_by_branch(self, prs: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Group PRs by branch."""
        grouped = {}
        for pr in prs:
            branch = pr.get('base_branch', 'unknown')
            if branch not in grouped:
                grouped[branch] = []
            grouped[branch].append(pr)
        return grouped
    
    def _get_pr_author(self, pr: Dict[str, Any]) -> str:
        """Get PR author name."""
        if pr.get('user') and isinstance(pr['user'], dict):
            return pr['user'].get('login', 'unknown')
        return 'unknown'

    def _estimate_prompt_tokens(self, prompt: str) -> int:
        """Estimate token count for prompt."""
        return len(prompt.split()) * 1.3  # Rough estimation
    
    def _should_use_chunked_summarization(self, prs: List[Dict[str, Any]], prompt: str) -> bool:
        """Determine if chunked summarization should be used."""
        estimated_tokens = self._estimate_prompt_tokens(prompt)
        return estimated_tokens > 8000 or len(prs) > 50
    
    def _prepare_data_for_chunked_summarization(self, prs: List[Dict[str, Any]], time_range: str) -> str:
        """Prepare data for chunked summarization."""
        text_content = f"# Development Summary - Last {time_range}\n\n"
        text_content += f"Total PRs: {len(prs)}\n\n"
        
        # Group by branch
        grouped = self._group_prs_by_branch(prs)
        
        for branch, branch_prs in grouped.items():
            text_content += f"## {branch.upper()} Branch ({len(branch_prs)} PRs)\n\n"
            
            for pr in branch_prs:
                author = self._get_pr_author(pr)
                text_content += f"### PR #{pr['number']}: {pr['title']}\n"
                text_content += f"**Author**: {author}\n"
                text_content += f"**Merged**: {pr.get('merged_at', 'Unknown')}\n"
                text_content += f"**URL**: {pr.get('html_url', 'Unknown')}\n"
                
                # Add PR body if available
                body = pr.get('body', '') or ''
                if body:
                    text_content += f"**Description**: {body[:500]}{'...' if len(body) > 500 else ''}\n"
                
                # Add Linear details if available
                linear_details = pr.get('linear_details')
                if linear_details:
                    # Basic Linear info
                    linear_title = linear_details.get('title', '') or ''
                    linear_description = linear_details.get('description', '') or ''
                    linear_state_obj = linear_details.get('state', {}) or {}
                    linear_state = linear_state_obj.get('name', '') or '' if linear_state_obj and isinstance(linear_state_obj, dict) else ''
                    linear_priority = linear_details.get('priority', '') or ''
                    
                    # Get labels safely
                    linear_labels = []
                    labels_obj = linear_details.get('labels', {}) or {}
                    if labels_obj and isinstance(labels_obj, dict):
                        label_nodes = labels_obj.get('nodes', []) or []
                        for label in label_nodes:
                            if label and isinstance(label, dict):
                                label_name = label.get('name', '') or ''
                                if label_name:
                                    linear_labels.append(label_name)
                    
                    # Enhanced Linear context
                    linear_assignee = linear_details.get('assignee', {}) or {}
                    linear_project = linear_details.get('project', {}) or {}
                    linear_team = linear_details.get('team', {}) or {}
                    linear_cycle = linear_details.get('cycle', {}) or {}
                    linear_comments_obj = linear_details.get('comments', {}) or {}
                    linear_comments = linear_comments_obj.get('nodes', []) or [] if linear_comments_obj and isinstance(linear_comments_obj, dict) else []
                    
                    if linear_title and linear_title != pr['title']:
                        text_content += f"**Linear Issue**: {linear_title}\n"
                    if linear_description:
                        desc_preview = linear_description[:500] + "..." if len(linear_description) > 500 else linear_description
                        text_content += f"**Linear Description**: {desc_preview}\n"
                    if linear_state:
                        text_content += f"**Linear Status**: {linear_state}\n"
                    if linear_priority:
                        text_content += f"**Linear Priority**: {linear_priority}\n"
                    if linear_labels:
                        text_content += f"**Linear Labels**: {', '.join(linear_labels)}\n"
                    if linear_assignee and isinstance(linear_assignee, dict) and linear_assignee.get('name'):
                        text_content += f"**Linear Assignee**: {linear_assignee['name']}\n"
                    if linear_project and isinstance(linear_project, dict) and linear_project.get('name'):
                        text_content += f"**Linear Project**: {linear_project['name']}\n"
                        if linear_project.get('description'):
                            proj_desc = linear_project['description'][:200] + "..." if len(linear_project['description']) > 200 else linear_project['description']
                            text_content += f"**Project Description**: {proj_desc}\n"
                    if linear_team and isinstance(linear_team, dict) and linear_team.get('name'):
                        text_content += f"**Linear Team**: {linear_team['name']} ({linear_team.get('key', '')})\n"
                    if linear_cycle and isinstance(linear_cycle, dict) and linear_cycle.get('name'):
                        text_content += f"**Linear Cycle**: {linear_cycle['name']} (#{linear_cycle.get('number', '')})\n"
                    
                    # Include recent comments for context
                    if linear_comments:
                        text_content += f"**Linear Comments**:\n"
                        for comment in linear_comments[-3:]:  # Last 3 comments
                            if comment and isinstance(comment, dict):
                                comment_body = comment.get('body', '') or ''
                                comment_user_obj = comment.get('user', {}) or {}
                                comment_user = comment_user_obj.get('name', 'Unknown') if comment_user_obj and isinstance(comment_user_obj, dict) else 'Unknown'
                                if comment_body:
                                    comment_preview = comment_body[:150] + "..." if len(comment_body) > 150 else comment_body
                                    text_content += f"  - {comment_user}: {comment_preview}\n"
                
                text_content += "\n---\n\n"
        
        return text_content
    
    def generate_beautiful_summary(self, prs: List[Dict[str, Any]], time_range: str) -> str:
        """Generate beautiful markdown summary using LLM."""
        if not prs:
            return "# 📊 No Pull Requests Found\n\nNo PRs were merged in the specified time range."
        
        if not self.openai_client:
            return "# ❌ OpenAI API Key Required\n\nPlease set OPENAI_API_KEY environment variable."
        
        # Extract Linear insights
        linear_insights = self._extract_linear_business_insights(prs)
        
        # Create prompt
        prompt = self.create_summary_prompt(prs, time_range)
        
        # Check if we should use chunked summarization
        if self._should_use_chunked_summarization(prs, prompt):
            print("🔄 Using chunked summarization for large dataset...")
            return self._generate_chunked_summary(prs, time_range, linear_insights)
        else:
            print("🔄 Using standard summarization...")
            return self._generate_standard_summary(prompt)
    
    def _generate_chunked_summary(self, prs: List[Dict[str, Any]], time_range: str, linear_insights: Dict[str, Any]) -> str:
        """Generate summary using chunked approach for large datasets."""
        try:
            # Prepare data for chunking
            text_content = self._prepare_data_for_chunked_summarization(prs, time_range)
            
            # Import chunked summarizer
            try:
                from chunked_summarizer import ChunkedSummarizer
                summarizer = ChunkedSummarizer(openai_key=self.openai_key)
                
                print("🔄 Using chunked summarization...")
                summary = summarizer.summarize_text(
                    text_content,
                    output_format="markdown",
                    max_words=300,
                    include_metadata=True
                )
                
                # Add Linear insights section
                if linear_insights['total_linear_items'] > 0:
                    summary += "\n\n" + self._create_linear_insights_section(linear_insights)
                
                print("✅ Chunked summary generated successfully!")
                return summary
                
            except ImportError:
                print("⚠️ Chunked summarizer not available, falling back to standard summary...")
                return self._generate_standard_summary(self.create_summary_prompt(prs, time_range))
            
        except Exception as e:
            print(f"❌ Error in chunked summarization: {e}")
            return self._generate_standard_summary(self.create_summary_prompt(prs, time_range))
    
    def _generate_standard_summary(self, prompt: str) -> str:
        """Generate standard summary using OpenAI."""
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an enthusiastic technical writer creating exciting weekly development digests. Use a celebratory, engaging tone with technical precision that gets teams pumped about their achievements. Focus on user impact, business wins, and technical excellence. Keep it concise (under 250 words) but make it fun to read and technically informative. Use action words, positive language, technical terminology, and highlight team accomplishments. Include relevant technical details like performance improvements, API enhancements, database optimizations, security updates, and scalability improvements. Think of this as a professional weekly newsletter that celebrates technical achievements while being accessible to both technical and non-technical stakeholders."
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
            print("✅ Standard summary generated successfully!")
            return summary
            
        except Exception as e:
            print(f"❌ Error generating summary: {e}")
            return f"# ❌ Summary Generation Failed\n\nError: {e}"
    
    def _create_linear_insights_section(self, linear_insights: Dict[str, Any]) -> str:
        """Create an exciting section for Linear insights."""
        section = "## 🔗 Linear Integration Highlights\n\n"
        
        section += f"🎯 **Total Linear Items**: {linear_insights['total_linear_items']}\n"
        
        if linear_insights['high_priority_items']:
            section += f"🔥 **High Priority Wins**: {len(linear_insights['high_priority_items'])} critical items completed!\n"
        
        if linear_insights['priority_distribution']:
            priorities = [f"{k}: {v}" for k, v in linear_insights['priority_distribution'].items()]
            section += f"📊 **Priority Breakdown**: {', '.join(priorities)}\n"
        
        if linear_insights['label_distribution']:
            top_labels = sorted(linear_insights['label_distribution'].items(), key=lambda x: x[1], reverse=True)[:5]
            labels = [f"{k} ({v})" for k, v in top_labels]
            section += f"🏷️ **Top Labels**: {', '.join(labels)}\n"
        
        return section

    def save_summary(self, summary: str, output_file: str) -> None:
        """Save summary to markdown file."""
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(summary)
            print(f"💾 Summary saved to: {output_file}")
        except Exception as e:
            print(f"❌ Error saving summary: {e}")

    def print_summary(self, summary: str) -> None:
        """Print summary to console."""
        print("\n" + "🎉" + "="*78 + "🎉")
        print("                    GITHUB PR SUMMARY")
        print("🎉" + "="*78 + "🎉")
        print(summary)
        print("🎉" + "="*78 + "🎉")

class SlackClient:
    """Handles Slack message sending with error handling and fallbacks."""
    
    def __init__(self, bot_token: Optional[str] = None, channel_id: Optional[str] = None):
        """Initialize Slack client."""
        self.bot_token = bot_token or os.getenv('SLACK_BOT_TOKEN')
        self.channel_id = channel_id or os.getenv('SLACK_CHANNEL_ID')
        
    def truncate_text(self, text: str, max_length: int = MAX_SLACK_TEXT_LENGTH) -> str:
        """Truncate text to fit Slack's limits."""
        if len(text) <= max_length:
            return text
        
        # Try to truncate at a sentence boundary
        truncated = text[:max_length-3]
        last_period = truncated.rfind('.')
        last_newline = truncated.rfind('\n')
        last_break = max(last_period, last_newline)
        
        if last_break > max_length * 0.8:  # If we can find a good break point
            return truncated[:last_break+1] + "..."
        else:
            return truncated + "..."
    
    def format_for_slack(self, markdown_text: str) -> str:
        """Convert markdown to Slack-friendly formatting."""
        if not markdown_text:
            return ""
        
        # Convert markdown to Slack formatting
        formatted = markdown_text
        
        # Headers - use bold with emojis (convert to Slack bold format)
        formatted = re.sub(r'^# (.+)$', r'*📊 \1*', formatted, flags=re.MULTILINE)
        formatted = re.sub(r'^## (.+)$', r'*\1*', formatted, flags=re.MULTILINE)
        formatted = re.sub(r'^### (.+)$', r'*\1*', formatted, flags=re.MULTILINE)
        

        
        # Bold text - convert **text** to *text* (Slack uses * for bold)
        formatted = re.sub(r'\*\*(.+?)\*\*', r'*\1*', formatted)
        
        # Italic text - convert *text* to _text_ (but not if it's already bold)
        formatted = re.sub(r'(?<!\*)\*([^*]+?)\*(?!\*)', r'_\1_', formatted)
        
        # Code blocks
        formatted = re.sub(r'```(.+?)```', r'`\1`', formatted, flags=re.DOTALL)
        
        # Inline code
        formatted = re.sub(r'`(.+?)`', r'`\1`', formatted)
        
        # Lists - convert to bullet points
        formatted = re.sub(r'^- (.+)$', r'• \1', formatted, flags=re.MULTILINE)
        formatted = re.sub(r'^\d+\. (.+)$', r'• \1', formatted, flags=re.MULTILINE)
        
        # Links - convert markdown links to Slack format (but preserve existing custom links)
        # First, temporarily replace existing custom links to protect them
        custom_links = re.findall(r'<https://[^>]+>', formatted)
        for i, link in enumerate(custom_links):
            formatted = formatted.replace(link, f'__CUSTOM_LINK_{i}__')
        
        # Convert markdown links to Slack format
        formatted = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<\2|\1>', formatted)
        
        # Restore custom links
        for i, link in enumerate(custom_links):
            formatted = formatted.replace(f'__CUSTOM_LINK_{i}__', link)
        
        # Clean up emoji codes and replace with actual emojis
        formatted = re.sub(r':bar_chart:', '📊', formatted)
        formatted = re.sub(r':date:', '📅', formatted)
        formatted = re.sub(r':alarm_clock:', '⏰', formatted)
        formatted = re.sub(r':rocket:', '🚀', formatted)
        formatted = re.sub(r':zap:', '⚡', formatted)
        formatted = re.sub(r':bug:', '🐛', formatted)
        formatted = re.sub(r':wrench:', '🔧', formatted)
        formatted = re.sub(r':busts_in_silhouette:', '👥', formatted)
        formatted = re.sub(r':robot_face:', '🤖', formatted)
        
        # Remove extra newlines and clean up spacing
        formatted = re.sub(r'\n{3,}', '\n\n', formatted)
        formatted = re.sub(r'•\s*\n\s*•', '•', formatted)  # Fix bullet point spacing
        
        return formatted.strip()
    
    def create_slack_blocks(self, summary: str, pr_count: int, time_range: str, repo: str, start_date=None, end_date=None, mvp_contributors=None) -> List[Dict[str, Any]]:
        """Create properly formatted Slack blocks."""
        formatted_summary = self.format_for_slack(summary)
        # Build time range string
        if start_date and end_date:
            time_range_str = f"Range: {start_date} to {end_date}"
        else:
            time_range_str = f"Time range: {time_range}"
        # Build MVP string
        mvp_str = ""
        if mvp_contributors:
            mvp_str = f"MVPs: {', '.join(mvp_contributors)}"
        blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*🚀 Weekly-Digest/{repo.split('/')[-1]}*"
                }
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"Range: {time_range_str}"
                    },
                    *([{ "type": "mrkdwn", "text": mvp_str }] if mvp_str else [])
                ]
            },
            {
                "type": "divider"
            }
        ]
        
        # Split the summary into sections and create blocks for each
        sections = formatted_summary.split('\n\n')
        current_section_text = ""
        
        for section in sections:
            section = section.strip()
            if not section:
                continue
                
            # Check if this is a section header (more flexible matching)
            # Remove formatting and check for header content
            section_clean = section.replace('*', '').replace('#', '').strip()
            if any(header in section_clean for header in [
                "*📊 This Week's Highlights*",
                "*🚀 What's New*", 
                "*⚡ Level Up*",
                "*🐛 Bug Squashed*",
                "*🔧 Behind the Scenes*"
            ]):
                # If we have accumulated text, add it as a section block
                if current_section_text.strip():
                    blocks.append({
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": current_section_text.strip()
                        }
                    })
                    # Add 1-line gap between sections
                    blocks.append({
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": " "
                        }
                    })
                    current_section_text = ""
                
                # Add the section header as a bold section block (mrkdwn)
                header_text_bold = f"*{section.replace('*', '').replace('#', '').strip()}*"
                blocks.append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": header_text_bold
                    }
                })
            else:
                # Accumulate text for the current section
                if current_section_text:
                    current_section_text += "\n\n" + section
                else:
                    current_section_text = section
        
        # Add any remaining text
        if current_section_text.strip():
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": current_section_text.strip()
                }
            })
        
        # Add footer
        blocks.extend([
            {
                "type": "divider"
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": "🤖 Powered by GitHub PR Analyzer | 🎉 Keep building amazing things!"
                    }
                ]
            }
        ])
        
        return blocks
    
    def send_message(self, blocks: List[Dict[str, Any]]) -> bool:
        """Send message to Slack using blocks format with fallback."""
        if not self.bot_token or not self.channel_id:
            print("❌ Slack bot token or channel ID not configured")
            return False
            
        headers = {
            "Authorization": f"Bearer {self.bot_token}",
            "Content-Type": "application/json"
        }
        
        # Try blocks format first
        payload = {
            "channel": self.channel_id,
            "blocks": blocks
        }
        
        try:
            response = requests.post(SLACK_API_BASE, headers=headers, json=payload)
            response.raise_for_status()
            
            result = response.json()
            if result.get('ok'):
                print("✅ Message sent to Slack successfully!")
                return True
            else:
                error = result.get('error')
                print(f"❌ Slack API error: {error}")
                
                # If blocks format failed, try simple text format
                if error == "invalid_blocks":
                    print("🔄 Trying fallback text format...")
                    return self.send_simple_message(self.extract_text_from_blocks(blocks))
                return False
                
        except Exception as e:
            print(f"❌ Error sending to Slack: {e}")
            return False
    
    def extract_text_from_blocks(self, blocks: List[Dict[str, Any]]) -> str:
        """Extract plain text from blocks for fallback message."""
        text_parts = []
        for block in blocks:
            if block.get('type') == 'header' and 'text' in block:
                text_parts.append(block['text'].get('text', ''))
            elif block.get('type') == 'section' and 'text' in block:
                text_parts.append(block['text'].get('text', ''))
            elif block.get('type') == 'context' and 'elements' in block:
                for element in block['elements']:
                    if element.get('type') == 'mrkdwn':
                        text_parts.append(element.get('text', ''))
        return '\n'.join(text_parts)
    
    def send_simple_message(self, text: str) -> bool:
        """Send a simple text message to Slack as fallback."""
        if not self.bot_token or not self.channel_id:
            return False
            
        headers = {
            "Authorization": f"Bearer {self.bot_token}",
            "Content-Type": "application/json"
        }
        
        # Truncate text to Slack's limit
        truncated_text = self.truncate_text(text, MAX_SLACK_SIMPLE_LENGTH)
        
        payload = {
            "channel": self.channel_id,
            "text": truncated_text
        }
        
        try:
            response = requests.post(SLACK_API_BASE, headers=headers, json=payload)
            response.raise_for_status()
            
            result = response.json()
            if result.get('ok'):
                print("✅ Fallback message sent to Slack successfully!")
                return True
            else:
                print(f"❌ Fallback message failed: {result.get('error')}")
                return False
                
        except Exception as e:
            print(f"❌ Error sending fallback message: {e}")
            return False
    
    def send_pr_summary(self, summary: str, pr_count: int, time_range: str, repo: str, start_date=None, end_date=None, mvp_contributors=None) -> bool:
        """Send PR summary to Slack with proper formatting."""
        blocks = self.create_slack_blocks(
            summary, pr_count, time_range, repo,
            start_date=start_date, end_date=end_date, mvp_contributors=mvp_contributors
        )
        return self.send_message(blocks)
    
    def send_error_notification(self, error_message: str, repo: str) -> bool:
        """Send error notification to Slack."""
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "mrkdwn",
                    "text": "*❌ Development Summary Generation Failed*"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"Failed to generate development summary for {repo}: {error_message}"
                }
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}"
                    }
                ]
            }
        ]
        
        return self.send_message(blocks) 

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


def main() -> None:
    """Main function to run the PR analyzer."""
    parser = argparse.ArgumentParser(description='GitHub PR Analyzer with Linear Integration and Slack Support')
    parser.add_argument('repo', help='Repository name (e.g., DrivetrainAi/drive)')
    parser.add_argument('--branches', nargs='+', default=DEFAULT_BRANCHES, 
                       help=f'Branches to analyze (default: {" ".join(DEFAULT_BRANCHES)})')
    parser.add_argument('--time-range', default=DEFAULT_TIME_RANGE,
                       help='Time range (1w, 1m, 6m, 1y, custom:YYYY-MM-DD)')
    parser.add_argument('--output', help='Output markdown file')
    parser.add_argument('--github-token', help='GitHub token')
    parser.add_argument('--openai-key', help='OpenAI API key')
    parser.add_argument('--linear-token', help='Linear API key')
    parser.add_argument('--slack-bot-token', help='Slack bot token')
    parser.add_argument('--slack-channel-id', help='Slack channel ID')
    parser.add_argument('--send-to-slack', action='store_true', help='Send summary to Slack')
    parser.add_argument('--interactive', action='store_true', help='Interactive mode')
    parser.add_argument('--no-save-raw-data', action='store_false', dest='save_raw_data',
                       help='Disable saving raw GitHub data to JSON file')
    
    args = parser.parse_args()
    
    # Initialize analyzer and Slack client
    analyzer = GitHubPRAnalyzer(
        github_token=args.github_token,
        openai_key=args.openai_key,
        linear_token=args.linear_token,
        save_raw_data=args.save_raw_data
    )
    
    slack_client = SlackClient(
        bot_token=args.slack_bot_token,
        channel_id=args.slack_channel_id
    )
    
    try:
        # Check for required tokens
        if not analyzer.github_token:
            error_msg = "GitHub token is required for private repositories."
            print(f"❌ {error_msg}")
            if args.send_to_slack:
                slack_client.send_error_notification(error_msg, args.repo)
            return
        
        if not analyzer.openai_key:
            error_msg = "OpenAI API key is required for generating summaries."
            print(f"❌ {error_msg}")
            if args.send_to_slack:
                slack_client.send_error_notification(error_msg, args.repo)
            return
        
        # Get time range
        time_range = args.time_range
        if args.interactive or not time_range:
            time_range = get_user_time_range()
        
        # Get start and end date for display
        start_date, end_date = analyzer.get_time_range(time_range)

        print(f"\n🚀 Analyzing PRs from {args.repo}")
        print(f"📅 Time range: {time_range}")
        print(f"🌿 Branches: {', '.join(args.branches)}")
        
        # Fetch PRs
        prs = analyzer.fetch_prs(args.repo, args.branches, time_range)

        # Debug: Print PRs fetched
        print("Fetched PRs:")
        for pr in prs:
            author = analyzer._get_pr_author(pr)
            print(f"  PR #{pr['number']} by {author} merged at {pr.get('merged_at')}")

        if not prs:
            message = "No PRs found in the specified time range."
            print(f"❌ {message}")
            if args.send_to_slack:
                slack_client.send_error_notification(message, args.repo)
            return
        
        print(f"✅ Found {len(prs)} PRs")
        
        # Calculate MVP contributors
        stats = analyzer._extract_statistics(prs)
        mvp_contributors = [author for author, _ in stats.get('top_authors', [])[:4]]

        # Generate summary
        summary = analyzer.generate_beautiful_summary(prs, time_range)

        # Format summary with PR links
        # formatted_summary = analyzer._format_summary_with_links(summary, prs, args.repo)
        formatted_summary = summary

        # Count PRs for stats
        pr_matches = re.findall(r'#(\d+)', summary)
        pr_count = len(set(pr_matches))

        # Save to file
        if args.output:
            analyzer.save_summary(formatted_summary, args.output)
        else:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            default_filename = f"development_summary_{timestamp}.md"
            analyzer.save_summary(formatted_summary, default_filename)

        # Print to console
        analyzer.print_summary(formatted_summary)

        # Send to Slack if requested
        if args.send_to_slack:
            success = slack_client.send_pr_summary(
                formatted_summary, pr_count, time_range, args.repo,
                start_date=start_date, end_date=end_date, mvp_contributors=mvp_contributors
            )
            if not success:
                print("⚠️ Failed to send to Slack, but summary was generated successfully")
        
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        print(f"❌ {error_msg}")
        if args.send_to_slack:
            slack_client.send_error_notification(error_msg, args.repo)
        sys.exit(1)


if __name__ == '__main__':
    main() 