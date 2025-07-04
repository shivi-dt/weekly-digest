#!/usr/bin/env python3
"""
Setup script for GitHub PR Analyzer & Executive Summary Generator
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="weekly-digest",
    version="1.0.0",
    author="Development Team",
    description="GitHub PR Analyzer & Executive Summary Generator for business stakeholders",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/your-org/weekly-digest",
    py_modules=["github_pr_analyzer", "chunked_summarizer"],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Software Development :: Documentation",
        "Topic :: Text Processing :: Linguistic",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "github-pr-analyzer=github_pr_analyzer:main",
            "chunked-summarizer=chunked_summarizer:main",
        ],
    },
    keywords="github, pull-requests, summary, ai, openai, slack, linear, business",
    project_urls={
        "Bug Reports": "https://github.com/your-org/weekly-digest/issues",
        "Source": "https://github.com/your-org/weekly-digest",
    },
) 