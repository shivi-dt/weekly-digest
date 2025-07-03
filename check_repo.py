#!/usr/bin/env python3
"""
Helper script to check repository access and available branches.
"""

import requests
import os
import sys

def check_repo_access(repo: str, token: str = None):
    """Check if we can access the repository and list available branches."""
    
    headers = {
        'Accept': 'application/vnd.github.v3+json',
        'User-Agent': 'GitHub-Repo-Checker'
    }
    
    if token:
        headers['Authorization'] = f'token {token}'
    
    # Check repository access
    print(f"Checking access to repository: {repo}")
    repo_url = f"https://api.github.com/repos/{repo}"
    
    try:
        response = requests.get(repo_url, headers=headers)
        if response.status_code == 200:
            repo_data = response.json()
            print(f"✅ Repository accessible!")
            print(f"   Name: {repo_data['name']}")
            print(f"   Description: {repo_data.get('description', 'No description')}")
            print(f"   Private: {repo_data['private']}")
            print(f"   Default branch: {repo_data['default_branch']}")
        else:
            print(f"❌ Repository not accessible: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error checking repository: {e}")
        return False
    
    # List branches with pagination
    print(f"\nFetching all branches...")
    all_branches = []
    page = 1
    per_page = 100
    
    while True:
        branches_url = f"https://api.github.com/repos/{repo}/branches"
        params = {
            'page': page,
            'per_page': per_page
        }
        
        try:
            response = requests.get(branches_url, headers=headers, params=params)
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
                return False
        except Exception as e:
            print(f"❌ Error fetching branches: {e}")
            return False
    
    print(f"✅ Found {len(all_branches)} branches:")
    
    # Sort branches for better readability
    all_branches.sort()
    
    # Look for main-v2 and main-v3 specifically
    main_v2_exists = 'main-v2' in all_branches
    main_v3_exists = 'main-v3' in all_branches
    
    if main_v2_exists:
        print(f"   ✅ main-v2 (production branch)")
    else:
        print(f"   ❌ main-v2 (not found)")
    
    if main_v3_exists:
        print(f"   ✅ main-v3 (production branch)")
    else:
        print(f"   ❌ main-v3 (not found)")
    
    # Show other branches (limit to first 20 to avoid overwhelming output)
    other_branches = [b for b in all_branches if b not in ['main-v2', 'main-v3']]
    if other_branches:
        print(f"\n   Other branches ({len(other_branches)} total):")
        for branch in other_branches[:20]:  # Show first 20
            print(f"   - {branch}")
        if len(other_branches) > 20:
            print(f"   ... and {len(other_branches) - 20} more branches")
    
    return True

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python check_repo.py <repo> [token]")
        print("Example: python check_repo.py DrivetrainAi/drive")
        print("Example: python check_repo.py DrivetrainAi/drive your_token_here")
        sys.exit(1)
    
    repo = sys.argv[1]
    token = sys.argv[2] if len(sys.argv) > 2 else os.getenv('GITHUB_TOKEN')
    
    if not token:
        print("⚠️  No GitHub token provided. Using public access (may fail for private repos).")
        print("   Set GITHUB_TOKEN environment variable or pass token as second argument.")
    
    check_repo_access(repo, token) 