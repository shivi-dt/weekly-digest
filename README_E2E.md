# 🚀 GitHub PR Analyzer - E2E Solution

**One command to fetch PRs and generate beautiful summaries!**

## ✨ Features

- 🎯 **Single Command** - Fetch PRs + Generate Summary in one go
- 🎨 **Beautiful Output** - Concise, well-formatted markdown summaries
- ⚡ **Fast & Efficient** - Optimized for quick analysis
- 📊 **Business Focused** - Highlights key changes and contributors
- 🔧 **Flexible** - Interactive mode or command-line options

## 🚀 Quick Start

### 1. Set up API Keys
```bash
export GITHUB_TOKEN=your_github_token_here
export OPENAI_API_KEY=your_openai_key_here
```

### 2. Run the Analyzer
```bash
# Interactive mode (recommended)
python github_pr_analyzer.py DrivetrainAi/drive --interactive

# Quick command
python github_pr_analyzer.py DrivetrainAi/drive --time-range 1w
```

## 📋 Usage Examples

### Interactive Mode
```bash
python github_pr_analyzer.py DrivetrainAi/drive --interactive
```
You'll be prompted to select:
- ⏰ Time range (1w, 1m, 6m, 1y, custom dates)
- 🌿 Branches to analyze
- 💾 Output file (optional)

### Command Line
```bash
# Last week
python github_pr_analyzer.py DrivetrainAi/drive --time-range 1w

# Last month
python github_pr_analyzer.py DrivetrainAi/drive --time-range 1m

# Custom date range
python github_pr_analyzer.py DrivetrainAi/drive --time-range custom:2024-06-01:2024-06-30

# Specific output file
python github_pr_analyzer.py DrivetrainAi/drive --time-range 1w --output my_summary.md
```

## 📊 Sample Output

```
🎉================================================================================🎉
                    GITHUB PR SUMMARY
🎉================================================================================🎉

# 🚀 Production Deployment Summary - Last Week

## 🚀 New Features
- **Enhanced Data Processing Pipeline**: New DTML generation capabilities with support for data dimension transformations
- **ECS Task ARN Management**: Ability to store and update ECS task ARNs for connection instances
- **Hubspot Metadata Retrieval**: New functionality to fetch table metadata for Hubspot connectors
- **Public API Migration**: Critical API endpoints moved to public API for better accessibility

## ⚡ Enhancements
- **Performance Optimizations**: Parallel processing for reconciliation operations
- **User Experience Improvements**: Automatic field population in connection requests
- **Logging Enhancements**: Better traceability and debugging capabilities
- **API Accessibility**: Improved external integration support

## 🐛 Bug Fixes
- **Dataset Loading Issues**: Resolved problems with dataset retrieval across multiple features
- **Connection ID Accuracy**: Fixed table metadata fetching using internal instance IDs
- **Workflow Reliability**: Prevented duplicate fetch workflows and ensured smooth operation
- **Boolean Filter Conditions**: Fixed incorrect handling of empty strings in filters
- **Board Creation Logic**: Improved draft board creation and management

## 🔧 Technical Improvements
- **Database Query Optimization**: Enhanced performance for faster response times
- **Security Enhancements**: Improved authentication and authorization mechanisms
- **Code Quality**: Better error handling and exception management
- **Infrastructure Updates**: Enhanced monitoring and alerting capabilities

## 👥 Top Contributors
1. **lomashSharma02** (8 PRs) - Data processing and API improvements
2. **manav-dt** (6 PRs) - User experience and frontend enhancements
3. **piyushdtai** (5 PRs) - Bug fixes and system stability
4. **sateesh-dt** (4 PRs) - Security and infrastructure improvements
5. **hexhog** (3 PRs) - Performance optimizations

## 📊 Quick Stats
- **Total PRs**: 66
- **New Features**: 4
- **Enhancements**: 4
- **Bug Fixes**: 5
- **Technical Improvements**: 4
- **Lines Changed**: +1,234 -156
- **Files Modified**: 45

---
*Generated on 2024-06-25*
🎉================================================================================🎉
```

## 🔧 Configuration

### Environment Variables
```bash
export GITHUB_TOKEN=your_github_token_here
export OPENAI_API_KEY=your_openai_key_here
```

### Command Line Options
```bash
python github_pr_analyzer.py REPO [OPTIONS]

Options:
  --branches BRANCHES     Branches to analyze (default: main-v2 main-v3)
  --time-range RANGE      Time range (1w, 1m, 6m, 1y, custom:YYYY-MM-DD)
  --output FILE           Output markdown file
  --github-token TOKEN    GitHub token
  --openai-key KEY        OpenAI API key
  --interactive           Interactive mode
```

## 🎯 Perfect For

- 📋 **Weekly Reports** - Generate deployment summaries for stakeholders
- 📊 **Release Notes** - Create beautiful release documentation
- 👥 **Team Updates** - Share progress with team members
- 📈 **Progress Tracking** - Monitor development activity over time

## 💡 Tips

- Use `--interactive` for the best experience
- The summary focuses on the most important changes
- Output is saved as markdown for easy sharing
- Perfect for weekly standups and stakeholder updates

---

**Ready to generate beautiful PR summaries? Run the analyzer now! 🚀** 