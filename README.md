# GitHub PR Analyzer & Executive Summary Generator

A comprehensive toolkit for analyzing GitHub Pull Requests and creating business-friendly executive summaries from large documents using AI.

## 🚀 Tools Included

### 1. GitHub PR Analyzer (`github_pr_analyzer.py`)
Analyzes GitHub Pull Requests and creates executive summaries for business stakeholders.

### 2. Executive Summary Generator (`chunked_summarizer.py`)
Splits large documents into chunks and creates perfect executive summaries with business-friendly language.

---

## 📋 GitHub PR Analyzer

### Features
- 🔍 Fetches PRs from main-v3 branch
- 🤖 Generates brief, article-style summaries using OpenAI GPT-4o-mini
- 📝 Creates concise updates (under 200 words) that read like newspaper articles
- 📱 Sends formatted messages to Slack with proper formatting
- ⏰ Supports various time ranges (1w, 1m, 6m, 1y, custom)
- 🚀 Automated via GitHub Actions
- 💾 Raw data storage for analysis and debugging
- 🎯 **Simple and readable** - Focuses on business impact and user value
- 🔗 **Enhanced Linear Integration** - Extracts Linear issue details and includes relevant links
- 🔄 **Smart Chunked Summarization** - Automatically uses chunked summarization for large datasets

### Quick Start

```bash
# Basic usage
python github_pr_analyzer.py DrivetrainAi/drive --send-to-slack

# Advanced usage
python github_pr_analyzer.py DrivetrainAi/drive \
  --time-range "1w" \
  --branches main-v3 \
  --output summary.md \
  --send-to-slack
```

### Setup
```bash
export GITHUB_TOKEN=your_github_token
export OPENAI_API_KEY=your_openai_api_key
export SLACK_BOT_TOKEN=your_slack_bot_token
export SLACK_CHANNEL_ID=your_slack_channel_id
export LINEAR_API_KEY=your_linear_api_key  # Optional: for enhanced Linear integration
```

### Linear Integration Features
When `LINEAR_API_KEY` is configured, the analyzer provides enhanced business context:

- **📋 Issue Details**: Extracts Linear issue titles, descriptions, and status
- **⚡ Priority Analysis**: Identifies high-priority items and business impact
- **🏷️ Label Insights**: Analyzes work categories and team focus areas
- **📊 Business Metrics**: Provides priority distribution and completion statistics
- **🎯 Enhanced Summaries**: Uses Linear context for more accurate business descriptions

Linear IDs are automatically detected from PR titles and descriptions using patterns like:
- `ENG-55822(fix):` - Enhanced pattern with type prefix
- `[ABC-123]` - Bracketed format
- `ABC-123:` - Direct format with colon
- `ABC-123` - Direct format  
- `Linear: ABC-123` - Explicit format
- `Issue: ABC-123` - Issue format

**Enhanced Linear Context Includes:**
- **Detailed Descriptions**: Full issue descriptions and business requirements
- **Team & Project Info**: Team assignments, project context, and strategic initiatives
- **Priority & Status**: Business importance and current state
- **Comments & Discussions**: Recent comments providing additional context
- **Cycle & Timeline**: Sprint/cycle information and due dates

### Smart Chunked Summarization
The analyzer automatically detects large datasets and switches to chunked summarization:

- **📊 Large Dataset Detection**: Automatically detects when PR count exceeds 50 or prompt size exceeds 15K tokens
- **🔄 Seamless Switching**: Transitions between standard and chunked summarization without user intervention
- **💰 Cost Estimation**: Provides cost estimates before processing large datasets
- **📝 Enhanced Quality**: Better summaries for repositories with many PRs or complex Linear data
- **🛡️ Fallback Protection**: Gracefully falls back to standard summarization if chunked processing fails

**When chunked summarization is used:**
- Large repositories with 50+ PRs in the time range
- Complex Linear integration with detailed issue descriptions
- Long time ranges (1m, 6m, 1y) with substantial development activity

---

## 📄 Executive Summary Generator

### Features
- 🔪 Smart chunking into ~10K token chunks for massive documents
- 🤖 AI-powered summarization with GPT-4o-mini
- 🔄 Robust retry logic with exponential backoff
- 💰 Pre-processing cost estimation
- 📊 **Perfect executive summary format**: 1-paragraph overview (8-10 lines) + detailed sections
- 📝 Supports `.txt` and `.md` files
- 🎯 Word limit control (default: 300 words)
- 🎯 **Business-friendly language** - Accessible to non-technical stakeholders

### Quick Start

```bash
# Basic usage
python chunked_summarizer.py document.txt

# Estimate cost only
python chunked_summarizer.py document.txt --estimate-only

# Custom settings
python chunked_summarizer.py document.txt \
  --chunk-size 8000 \
  --max-words 500 \
  --output executive_summary.md
```

### Setup
```bash
export OPENAI_API_KEY=your_openai_api_key
```

---

## 🛠️ Installation

### Quick Install (Recommended)
```bash
# Clone the repository
git clone <your-repo-url>
cd weekly-digest

# Run the installation script
./install.sh
```

### Manual Installation
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install in development mode (optional)
pip install -e .
```

### Test Installation
```bash
# Verify everything is working
python test_setup.py
```

### Dependencies
- `requests>=2.31.0` - HTTP requests
- `openai>=1.0.0` - OpenAI API client
- `PyGithub>=2.0.0` - GitHub API client
- `tiktoken` - Token counting (for chunked summarizer)

---

## 📖 Detailed Documentation

### GitHub PR Analyzer

| Option | Description | Default |
|--------|-------------|---------|
| `repo` | Repository name (e.g., DrivetrainAi/drive) | Required |
| `--branches` | Branches to analyze | main-v2 main-v3 |
| `--time-range` | Time range (1w, 1m, 6m, 1y, custom:YYYY-MM-DD) | 1w |
| `--output` | Output markdown file | Auto-generated |
| `--send-to-slack` | Send summary to Slack | False |
| `--interactive` | Interactive mode for time range selection | False |
| `--no-save-raw-data` | Disable saving raw GitHub data to JSON file | False |

### Executive Summary Generator

| Option | Description | Default |
|--------|-------------|---------|
| `input_file` | Input file (.txt or .md) | Required |
| `--output, -o` | Output file | `summary.md` |
| `--openai-key` | OpenAI API key | `OPENAI_API_KEY` env var |
| `--chunk-size` | Max tokens per chunk | 10,000 |
| `--max-words` | Max words in final summary | 300 |
| `--estimate-only` | Only estimate cost, don't process | False |

---

## 🔧 GitHub Actions

The workflow runs automatically:
- Every Monday at 9 AM UTC
- On pushes to the main branch

### Required Secrets
- `GITHUB_TOKEN` (automatically provided)
- `OPENAI_API_KEY`
- `SLACK_BOT_TOKEN`
- `SLACK_CHANNEL_ID`

---

## 💡 Use Cases

### GitHub PR Analyzer
- **Weekly executive summaries** for senior leadership
- **Business stakeholder reports** from development work
- **Non-technical team updates** about software changes
- **Automated Slack notifications** for business teams

### Executive Summary Generator
- **Large business reports** and quarterly updates
- **Meeting minutes** and documentation processing
- **Research papers** and technical documents
- **Code review summaries** for business stakeholders

---

## 🎯 Example Workflows

### Daily Executive Summary
```bash
# Summarize today's changes for business stakeholders
python github_pr_analyzer.py DrivetrainAi/drive \
  --time-range "custom:2024-07-03:2024-07-03" \
  --send-to-slack
```

### Large Document Processing
```bash
# Process a large business report
python chunked_summarizer.py quarterly_report.txt \
  --chunk-size 15000 \
  --max-words 500 \
  --output executive_summary.md
```

### Combined Workflow
```bash
# Generate PR summary
python github_pr_analyzer.py DrivetrainAi/drive --time-range "1w" --output pr_summary.md

# Further summarize for executives
python chunked_summarizer.py pr_summary.md --max-words 200 --output executive_summary.md
```

---

## 🚨 Troubleshooting

### Common Issues

1. **API Key Errors**
   - Ensure environment variables are set correctly
   - Check API key permissions and credits

2. **File Not Found**
   - Verify file paths and permissions
   - Check file extensions (.txt, .md)

3. **Rate Limiting**
   - Tools automatically retry with exponential backoff
   - Consider upgrading API plans for high usage

4. **High Costs**
   - Use `--estimate-only` to check costs first
   - Adjust chunk sizes and word limits as needed

### Performance Tips

- **Large documents**: Use larger chunk sizes (15K-20K tokens)
- **Complex content**: Use smaller chunk sizes (5K-8K tokens)
- **Cost optimization**: Use `--estimate-only` before processing
- **Quality focus**: Use default settings for best results

---

## 📊 Output Examples

### GitHub PR Executive Summary
```markdown
# 📊 Development Summary - DrivetrainAi/drive

## 📊 Quick Stats
- **Total Changes**: 15 pull requests
- **Active Contributors**: 8 developers
- **Lines Changed**: +2,450 / -890
- **Time Period**: Last week

## 🚀 New Features
- **Enhanced Security**: Implemented multi-factor authentication system ([#123](https://github.com/DrivetrainAi/drive/pull/123))
- **Mobile Enhancement**: Added new features to improve user engagement ([#125](https://github.com/DrivetrainAi/drive/pull/125))
- **Real-time Chat**: WebSocket-based messaging system for team collaboration ([#127](https://github.com/DrivetrainAi/drive/pull/127))

## 🐛 Bug Fixes
- **Performance Issues**: Resolved critical system slowdowns affecting user experience ([#124](https://github.com/DrivetrainAi/drive/pull/124))
- **Security Vulnerabilities**: Fixed authentication system vulnerabilities ([#126](https://github.com/DrivetrainAi/drive/pull/126))
- **Database Errors**: Resolved connection timeout issues ([#128](https://github.com/DrivetrainAi/drive/pull/128))

## ⚡ Enhancements & Improvements
- **User Experience**: Simplified login process and improved interface design ([#129](https://github.com/DrivetrainAi/drive/pull/129))
- **System Reliability**: Enhanced error handling and monitoring capabilities ([#130](https://github.com/DrivetrainAi/drive/pull/130))
- **Customer Support**: Improved response times and issue resolution ([#131](https://github.com/DrivetrainAi/drive/pull/131))
```

### Executive Summary Generator
```markdown
# 📊 Executive Summary

Our organization achieved exceptional results in Q1 2024, with 35% revenue growth driven by successful market expansion into three new regions and significant operational efficiency improvements. We successfully launched a new mobile application that exceeded adoption targets with 10,000 downloads in the first month, implemented comprehensive process automation that reduced operational costs by 25%, and enhanced customer satisfaction scores by 20% through improved service quality initiatives. These achievements position us strongly for continued growth and market leadership in the coming quarters.

## Major Accomplishments
- **Market Expansion**: Successfully launched operations in three new regional markets
- **Product Launch**: Developed and launched new mobile application with strong adoption
- **Revenue Growth**: Achieved 35% revenue increase while maintaining healthy margins

## Key Improvements
- **Operational Efficiency**: 50% reduction in processing time through automation
- **Customer Experience**: 40% improvement in user satisfaction scores
- **Cost Management**: 12% reduction in overall operational costs

## Business Impact
- **Customer Acquisition**: 40% increase in website traffic and 25% improvement in lead generation
- **Employee Development**: Hired 25 new employees with high satisfaction scores
- **Risk Management**: Enhanced cybersecurity and regulatory compliance

---
*Generated from 156 words (423 tokens)*
```

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test locally
5. Submit a pull request

---

## 📄 License

MIT License - see LICENSE file for details. 