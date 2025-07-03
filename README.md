# GitHub PR Fetcher

A Python script to fetch Pull Requests from GitHub repositories with configurable time ranges and branch filtering.

## Features

- Fetch PRs merged to specific branches (e.g., main-v2, main-v3)
- Configurable time ranges (1 week, 1 month, 6 months, 1 year)
- Export data to JSON format for LLM processing
- Filter by merge date
- Comprehensive PR data including commits, additions, deletions, and file changes

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. (Optional) Set up GitHub token for higher rate limits:
```bash
export GITHUB_TOKEN=your_github_token_here
```

## Usage

### Basic Usage

Fetch PRs from the last week merged to main-v2 and main-v3:
```bash
python github_pr_fetcher.py DrivetrainAi/drive
```

### Interactive Mode

Use interactive mode to choose your time range:
```bash
python github_pr_fetcher.py DrivetrainAi/drive --interactive
```

This will present you with options:
1. Last week (1w)
2. Last month (1m) 
3. Last 6 months (6m)
4. Last year (1y)
5. Custom start date (until now)
6. Custom start and end dates

### Advanced Usage

Fetch PRs from the last month:
```bash
python github_pr_fetcher.py DrivetrainAi/drive --time-range 1m
```

Fetch PRs from specific branches:
```bash
python github_pr_fetcher.py DrivetrainAi/drive --branches main-v2 main-v3 main
```

Save to specific file:
```bash
python github_pr_fetcher.py DrivetrainAi/drive --output my_prs.json
```

Use custom GitHub token:
```bash
python github_pr_fetcher.py DrivetrainAi/drive --token your_token_here
```

### Time Range Options

- `1w`: Last week
- `1m`: Last month (30 days)
- `6m`: Last 6 months (180 days)
- `1y`: Last year (365 days)
- `custom:YYYY-MM-DD`: From specific date until now
- `custom:YYYY-MM-DD:YYYY-MM-DD`: From start date to end date
- Interactive mode: Choose from menu

### Output Format

The script generates a JSON file with detailed PR information including:

- PR number and title
- Author and assignees
- Base branch
- Merge, creation, and update dates
- URL and description
- Labels and reviewers
- Commit statistics (additions, deletions, changed files)

## Example Output

```json
[
  {
    "number": 123,
    "title": "Add new feature",
    "author": "username",
    "base_branch": "main-v2",
    "merged_at": "2024-01-15T10:30:00Z",
    "created_at": "2024-01-10T14:20:00Z",
    "updated_at": "2024-01-15T10:30:00Z",
    "url": "https://github.com/DrivetrainAi/drive/pull/123",
    "body": "PR description...",
    "labels": ["enhancement"],
    "assignees": ["reviewer1"],
    "reviewers": ["reviewer2"],
    "commits_count": 5,
    "additions": 150,
    "deletions": 25,
    "changed_files": 8
  }
]
```

## GitHub Token Setup

For higher rate limits and access to private repositories, create a GitHub personal access token:

1. Go to GitHub Settings → Developer settings → Personal access tokens
2. Generate a new token with `repo` scope
3. Set as environment variable: `export GITHUB_TOKEN=your_token`

## Rate Limits

- Without token: 60 requests/hour
- With token: 5000 requests/hour

The script handles rate limiting gracefully and will pause if limits are exceeded. 