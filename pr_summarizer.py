#!/usr/bin/env python3
"""
GitHub PR Summarizer
Uses LLM to generate markdown summaries from GitHub PR data.
"""

import json
import argparse
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
import openai
from openai import OpenAI

class PRSummarizer:
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o-mini"):
        """
        Initialize the PR summarizer.
        
        Args:
            api_key: OpenAI API key (optional, can be set via OPENAI_API_KEY env var)
            model: OpenAI model to use for summarization
        """
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        self.model = model
        
        if not self.api_key:
            raise ValueError("OpenAI API key is required. Set OPENAI_API_KEY environment variable or pass --api-key")
        
        self.client = OpenAI(api_key=self.api_key)
    
    def load_pr_data(self, json_file: str) -> List[Dict[str, Any]]:
        """
        Load PR data from JSON file.
        
        Args:
            json_file: Path to JSON file containing PR data
            
        Returns:
            List of PR data dictionaries
        """
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if not isinstance(data, list):
                raise ValueError("JSON file should contain a list of PR objects")
            
            print(f"✅ Loaded {len(data)} PRs from {json_file}")
            return data
        except FileNotFoundError:
            print(f"❌ File not found: {json_file}")
            return []
        except json.JSONDecodeError as e:
            print(f"❌ Invalid JSON in {json_file}: {e}")
            return []
        except Exception as e:
            print(f"❌ Error loading {json_file}: {e}")
            return []
    
    def group_prs_by_branch(self, prs: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Group PRs by their base branch.
        
        Args:
            prs: List of PR data
            
        Returns:
            Dictionary with branch names as keys and PR lists as values
        """
        grouped = {}
        for pr in prs:
            branch = pr.get('base_branch', 'unknown')
            if branch not in grouped:
                grouped[branch] = []
            grouped[branch].append(pr)
        
        return grouped
    
    def create_summary_prompt(self, prs: List[Dict[str, Any]], time_range: str) -> str:
        """
        Create a prompt for the LLM to summarize PRs.
        
        Args:
            prs: List of PR data
            time_range: Time range string for context
            
        Returns:
            Formatted prompt string
        """
        # Group PRs by branch
        grouped_prs = self.group_prs_by_branch(prs)
        
        prompt = f"""You are a technical writer tasked with creating a comprehensive markdown summary of Pull Requests merged to production branches.

Time Period: {time_range}
Total PRs: {len(prs)}

Please analyze the following Pull Requests and create a well-structured markdown summary that includes:

1. **Executive Summary** - High-level overview of changes
2. **Changes by Branch** - Group changes by production branch (main-v2, main-v3)
3. **Key Features & Improvements** - Notable new features or enhancements
4. **Bug Fixes** - Important bug fixes and issues resolved
5. **Technical Improvements** - Performance, security, or infrastructure changes
6. **Contributors** - List of developers who contributed
7. **Statistics** - Summary of changes (total additions, deletions, files changed)

Format the summary in clean markdown with proper headings, bullet points, and code formatting where appropriate.

Here are the PR details:

"""
        
        for branch, branch_prs in grouped_prs.items():
            prompt += f"\n## {branch.upper()} BRANCH ({len(branch_prs)} PRs)\n\n"
            
            for pr in branch_prs:
                prompt += f"### PR #{pr['number']}: {pr['title']}\n"
                prompt += f"- **Author**: {pr['author']}\n"
                prompt += f"- **Merged**: {pr['merged_at']}\n"
                prompt += f"- **URL**: {pr['url']}\n"
                
                if pr.get('body'):
                    # Truncate long descriptions
                    body = pr['body'][:500] + "..." if len(pr['body']) > 500 else pr['body']
                    prompt += f"- **Description**: {body}\n"
                
                if pr.get('labels'):
                    prompt += f"- **Labels**: {', '.join(pr['labels'])}\n"
                
                prompt += f"- **Changes**: +{pr.get('additions', 0)} -{pr.get('deletions', 0)} lines, {pr.get('changed_files', 0)} files\n"
                prompt += f"- **Commits**: {pr.get('commits_count', 0)}\n\n"
        
        prompt += """
Please create a comprehensive, well-organized markdown summary that would be useful for:
- Product managers reviewing what was deployed
- Developers understanding recent changes
- Stakeholders getting an overview of development activity

Focus on business value, user impact, and technical significance. Use clear, professional language.
"""
        
        return prompt
    
    def generate_summary(self, prs: List[Dict[str, Any]], time_range: str) -> str:
        """
        Generate markdown summary using LLM.
        
        Args:
            prs: List of PR data
            time_range: Time range string
            
        Returns:
            Generated markdown summary
        """
        if not prs:
            return "# No Pull Requests Found\n\nNo PRs were found in the specified time range."
        
        prompt = self.create_summary_prompt(prs, time_range)
        
        try:
            print("🤖 Generating summary with LLM...")
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a technical writer specializing in creating clear, comprehensive summaries of software development changes. Focus on business value and user impact."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,
                max_tokens=4000
            )
            
            summary = response.choices[0].message.content
            print("✅ Summary generated successfully!")
            return summary
            
        except Exception as e:
            print(f"❌ Error generating summary: {e}")
            return f"# Error Generating Summary\n\nAn error occurred while generating the summary: {e}"
    
    def save_summary(self, summary: str, output_file: str):
        """
        Save summary to markdown file.
        
        Args:
            summary: Generated markdown summary
            output_file: Output file path
        """
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(summary)
            print(f"✅ Summary saved to {output_file}")
        except Exception as e:
            print(f"❌ Error saving summary: {e}")
    
    def print_summary(self, summary: str):
        """
        Print summary to console.
        
        Args:
            summary: Generated markdown summary
        """
        print("\n" + "="*80)
        print("GENERATED SUMMARY")
        print("="*80)
        print(summary)
        print("="*80)


def main():
    parser = argparse.ArgumentParser(description='Generate markdown summary of GitHub PRs using LLM')
    parser.add_argument('json_file', help='JSON file containing PR data')
    parser.add_argument('--output', help='Output markdown file (optional)')
    parser.add_argument('--api-key', help='OpenAI API key (optional, can use OPENAI_API_KEY env var)')
    parser.add_argument('--model', default='gpt-4o-mini', 
                       help='OpenAI model to use (default: gpt-4o-mini)')
    parser.add_argument('--time-range', default='recent', 
                       help='Time range for context (default: recent)')
    parser.add_argument('--no-print', action='store_true',
                       help='Don\'t print summary to console')
    
    args = parser.parse_args()
    
    # Initialize summarizer
    try:
        summarizer = PRSummarizer(api_key=args.api_key, model=args.model)
    except ValueError as e:
        print(f"❌ {e}")
        return
    
    # Load PR data
    prs = summarizer.load_pr_data(args.json_file)
    if not prs:
        return
    
    # Generate summary
    summary = summarizer.generate_summary(prs, args.time_range)
    
    # Save to file if requested
    if args.output:
        summarizer.save_summary(summary, args.output)
    else:
        # Generate default filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        default_filename = f"pr_summary_{timestamp}.md"
        summarizer.save_summary(summary, default_filename)
    
    # Print to console unless disabled
    if not args.no_print:
        summarizer.print_summary(summary)


if __name__ == '__main__':
    main() 