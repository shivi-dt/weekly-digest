#!/usr/bin/env python3
"""
Chunked Summarization Pipeline
Splits large documents into chunks, summarizes each, and merges into a final summary.
"""

import argparse
import json
import os
import re
import sys
import time
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

import tiktoken
from openai import OpenAI
from openai import RateLimitError, APIError, APIConnectionError

# Constants
MAX_CHUNK_TOKENS = 10000
MAX_FINAL_WORDS = 300
MAX_RETRIES = 3
RETRY_DELAY = 2
GPT4O_MINI_INPUT_COST_PER_1K = 0.00015
GPT4O_MINI_OUTPUT_COST_PER_1K = 0.0006

class Tokenizer:
    """Handles token counting and text chunking."""
    
    def __init__(self):
        """Initialize the tokenizer."""
        self.encoding = tiktoken.get_encoding('cl100k_base')
    
    def count_tokens(self, text: str) -> int:
        """Count tokens in text."""
        return len(self.encoding.encode(text))
    
    def split_into_chunks(self, text: str, max_tokens: int = MAX_CHUNK_TOKENS) -> List[str]:
        """Split text into chunks of approximately max_tokens."""
        if self.count_tokens(text) <= max_tokens:
            return [text]
        
        chunks = []
        current_chunk = ""
        sentences = self._split_into_sentences(text)
        
        for sentence in sentences:
            test_chunk = current_chunk + sentence + "\n\n"
            if self.count_tokens(test_chunk) <= max_tokens:
                current_chunk = test_chunk
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence + "\n\n"
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences while preserving structure."""
        # Split on sentence endings, but be careful with abbreviations
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return [s.strip() for s in sentences if s.strip()]


class ChunkedSummarizer:
    """Handles chunked summarization with retry logic."""
    
    def __init__(self, openai_key: Optional[str] = None):
        """Initialize the summarizer."""
        self.openai_key = openai_key or os.getenv('OPENAI_API_KEY')
        self.client = OpenAI(api_key=self.openai_key) if self.openai_key else None
        self.tokenizer = Tokenizer()
        
    def summarize_chunk(self, chunk: str, chunk_index: int, total_chunks: int) -> str:
        """Summarize a single chunk with retry logic."""
        if not self.client:
            raise ValueError("OpenAI client not initialized. Please set OPENAI_API_KEY.")
        
        prompt = self._create_chunk_prompt(chunk, chunk_index, total_chunks)
        
        for attempt in range(MAX_RETRIES):
            try:
                response = self.client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {
                            "role": "system",
                            "content": "You are an expert technical writer. Create concise, well-structured summaries using markdown and emojis. Focus on categorizing changes into: 🚀 New Features, 🐞 Bug Fixes, and 🧹 Improvements. Be specific and actionable."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    temperature=0.3,
                    max_tokens=1000
                )
                
                summary = response.choices[0].message.content
                print(f"✅ Chunk {chunk_index + 1}/{total_chunks} summarized successfully")
                return summary
                
            except (RateLimitError, APIError, APIConnectionError) as e:
                if attempt < MAX_RETRIES - 1:
                    wait_time = RETRY_DELAY * (2 ** attempt)
                    print(f"⚠️ Attempt {attempt + 1} failed: {e}. Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    print(f"❌ Failed to summarize chunk {chunk_index + 1} after {MAX_RETRIES} attempts")
                    return f"## Chunk {chunk_index + 1} Summary\n\n*Summary generation failed: {str(e)}*"
            
            except Exception as e:
                print(f"❌ Unexpected error summarizing chunk {chunk_index + 1}: {e}")
                return f"## Chunk {chunk_index + 1} Summary\n\n*Summary generation failed: {str(e)}*"
    
    def _create_chunk_prompt(self, chunk: str, chunk_index: int, total_chunks: int) -> str:
        """Create prompt for chunk summarization."""
        return f"""Analyze the following content (part {chunk_index + 1} of {total_chunks}) and create a brief summary:

{chunk}

Write a short, engaging summary that reads like a brief update. Focus on:

1. **What was accomplished** - Key changes, improvements, and technical enhancements
2. **Business impact** - How this affects users, operations, and system performance
3. **Notable highlights** - Most important points including technical achievements
4. **Technical details** - Relevant performance improvements, API changes, or system optimizations

Keep it:
- Simple and readable (like a newspaper article)
- Concise (under 100 words)
- Business-focused with technical precision
- Easy to scan while being technically informative

Use clear, professional language with appropriate technical terminology.

When Linear data is available, use it for better context and include relevant Linear issue links."""

    def merge_summaries(self, summaries: List[str]) -> str:
        """Merge multiple chunk summaries into a final summary."""
        if not summaries:
            return "# 📊 Executive Summary\n\nNo content was provided for analysis."
        
        if len(summaries) == 1:
            return self._format_final_summary(summaries[0])
        
        # Combine all summaries
        combined_content = "\n\n".join(summaries)
        
        # Create merge prompt for executive summary
        merge_prompt = f"""Create a brief, engaging summary from {len(summaries)} partial analyses.

Raw content from all sections:
{combined_content}

Write this as a short article or update, not a detailed report. Structure:

1. **Brief overview** (2-3 sentences) - What was accomplished overall
2. **Key highlights** (3-4 bullet points) - Most important changes

Requirements:
- Keep it under 250 words total
- Write in a conversational, article-style format with technical precision
- Focus on business impact, user benefits, and technical achievements
- Include relevant Linear issue links where helpful
- Make it easy to read quickly while being technically informative
- Use appropriate technical terminology and mention performance improvements

Create a summary that reads like a brief newspaper article about the week's development progress."""
        
        # Generate final summary
        for attempt in range(MAX_RETRIES):
            try:
                response = self.client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a technical writer creating brief, engaging updates about software development progress. Write in a conversational, article-style format with technical precision that's easy to read quickly. Focus on business impact, user benefits, and technical achievements. Keep summaries concise and include relevant links. Use appropriate technical terminology, mention performance improvements, and highlight system enhancements while remaining accessible to both technical and non-technical stakeholders."
                        },
                        {
                            "role": "user",
                            "content": merge_prompt
                        }
                    ],
                    temperature=0.2,
                    max_tokens=1000
                )
                
                final_summary = response.choices[0].message.content
                return self._format_final_summary(final_summary)
                
            except (RateLimitError, APIError, APIConnectionError) as e:
                if attempt < MAX_RETRIES - 1:
                    wait_time = RETRY_DELAY * (2 ** attempt)
                    print(f"⚠️ Merge attempt {attempt + 1} failed: {e}. Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    print(f"❌ Failed to merge summaries after {MAX_RETRIES} attempts")
                    return self._format_final_summary("\n\n".join(summaries))
            
            except Exception as e:
                print(f"❌ Unexpected error merging summaries: {e}")
                return self._format_final_summary("\n\n".join(summaries))
    
    def _format_final_summary(self, summary: str) -> str:
        """Format the final summary with metadata."""
        word_count = len(summary.split())
        token_count = self.tokenizer.count_tokens(summary)
        
        header = f"# 📊 Executive Summary\n\n"
        footer = f"\n\n---\n*Generated from {word_count} words ({token_count:,} tokens)*"
        
        return header + summary + footer
    
    def estimate_cost(self, text: str) -> Dict[str, float]:
        """Estimate the cost of processing the text."""
        total_tokens = self.tokenizer.count_tokens(text)
        chunks = self.tokenizer.split_into_chunks(text)
        
        # Estimate input tokens (all chunks)
        input_tokens = sum(self.tokenizer.count_tokens(chunk) for chunk in chunks)
        
        # Estimate output tokens (assume 20% of input for summaries)
        estimated_output_tokens = int(input_tokens * 0.2)
        
        # Final merge tokens
        merge_input_tokens = estimated_output_tokens
        merge_output_tokens = 800  # max_tokens for final summary
        
        total_input_cost = (input_tokens + merge_input_tokens) * GPT4O_MINI_INPUT_COST_PER_1K / 1000
        total_output_cost = (estimated_output_tokens + merge_output_tokens) * GPT4O_MINI_OUTPUT_COST_PER_1K / 1000
        
        return {
            "total_tokens": total_tokens,
            "chunks": len(chunks),
            "estimated_input_tokens": input_tokens + merge_input_tokens,
            "estimated_output_tokens": estimated_output_tokens + merge_output_tokens,
            "total_cost": total_input_cost + total_output_cost,
            "input_cost": total_input_cost,
            "output_cost": total_output_cost
        }

    def summarize_text(self, text: str, max_words: int = MAX_FINAL_WORDS) -> str:
        """Summarize text content using chunked approach."""
        if not self.client:
            raise ValueError("OpenAI client not initialized. Please set OPENAI_API_KEY.")
        
        # Split text into chunks
        chunks = self.tokenizer.split_into_chunks(text)
        
        if len(chunks) == 1:
            # Single chunk - use direct summarization
            return self._direct_summarize(text, max_words)
        
        # Multiple chunks - use chunked approach
        print(f"📝 Processing {len(chunks)} chunks...")
        
        # Summarize each chunk
        summaries = []
        for i, chunk in enumerate(chunks):
            print(f"📝 Processing chunk {i + 1}/{len(chunks)}...")
            summary = self.summarize_chunk(chunk, i, len(chunks))
            summaries.append(summary)
        
        # Merge summaries
        print("🔗 Merging summaries...")
        final_summary = self.merge_summaries(summaries)
        
        return final_summary

    def _direct_summarize(self, text: str, max_words: int) -> str:
        """Summarize text directly without chunking."""
        prompt = f"""Create a brief, engaging summary of the following content:

{text}

Write this as a short article or update, not a detailed report. Structure:

1. **Brief overview** (2-3 sentences) - What was accomplished overall
2. **Key highlights** (3-4 bullet points) - Most important changes

Requirements:
- Keep it under {max_words} words total
- Write in a conversational, article-style format with technical precision
- Focus on business impact, user benefits, and technical achievements
- Include relevant Linear issue links where helpful
- Make it easy to read quickly while being technically informative
- Use appropriate technical terminology and mention performance improvements

Create a summary that reads like a brief newspaper article about the development progress."""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a technical writer creating brief, engaging updates about software development progress. Write in a conversational, article-style format with technical precision that's easy to read quickly. Focus on business impact, user benefits, and technical achievements. Keep summaries concise and include relevant links. Use appropriate technical terminology, mention performance improvements, and highlight system enhancements while remaining accessible to both technical and non-technical stakeholders."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.2,
                max_tokens=1000
            )
            
            summary = response.choices[0].message.content
            return self._format_final_summary(summary)
            
        except Exception as e:
            print(f"❌ Error in direct summarization: {e}")
            return f"# ❌ Summary Generation Failed\n\nError: {e}"


def read_file(file_path: str) -> str:
    """Read file content, supporting both .txt and .md files."""
    path = Path(file_path)
    
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    if path.suffix.lower() not in ['.txt', '.md']:
        raise ValueError(f"Unsupported file type: {path.suffix}. Only .txt and .md files are supported.")
    
    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if not content.strip():
            raise ValueError("File is empty")
        
        return content
        
    except UnicodeDecodeError:
        raise ValueError(f"Unable to read file {file_path}. Please ensure it's a valid text file.")


def save_summary(summary: str, output_file: str) -> None:
    """Save summary to file."""
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(summary)
        print(f"💾 Summary saved to: {output_file}")
    except Exception as e:
        print(f"❌ Error saving summary: {e}")


def main() -> None:
    """Main function."""
    parser = argparse.ArgumentParser(description='Chunked Document Summarization Pipeline')
    parser.add_argument('input_file', help='Input file (.txt or .md)')
    parser.add_argument('--output', '-o', help='Output file (default: summary.md)')
    parser.add_argument('--openai-key', help='OpenAI API key')
    parser.add_argument('--chunk-size', type=int, default=MAX_CHUNK_TOKENS,
                       help=f'Maximum tokens per chunk (default: {MAX_CHUNK_TOKENS})')
    parser.add_argument('--max-words', type=int, default=MAX_FINAL_WORDS,
                       help=f'Maximum words in final summary (default: {MAX_FINAL_WORDS})')
    parser.add_argument('--estimate-only', action='store_true',
                       help='Only estimate cost and chunks, don\'t process')
    
    args = parser.parse_args()
    
    try:
        # Read input file
        print(f"📖 Reading file: {args.input_file}")
        content = read_file(args.input_file)
        
        # Create tokenizer for estimation
        tokenizer = Tokenizer()
        
        # Estimate cost and chunks
        print("🔍 Analyzing document...")
        total_tokens = tokenizer.count_tokens(content)
        chunks = tokenizer.split_into_chunks(content, args.chunk_size)
        
        # Calculate cost estimates
        input_tokens = sum(tokenizer.count_tokens(chunk) for chunk in chunks)
        estimated_output_tokens = int(input_tokens * 0.2)
        merge_input_tokens = estimated_output_tokens
        merge_output_tokens = 800
        
        total_input_cost = (input_tokens + merge_input_tokens) * GPT4O_MINI_INPUT_COST_PER_1K / 1000
        total_output_cost = (estimated_output_tokens + merge_output_tokens) * GPT4O_MINI_OUTPUT_COST_PER_1K / 1000
        total_cost = total_input_cost + total_output_cost
        
        cost_estimate = {
            "total_tokens": total_tokens,
            "chunks": len(chunks),
            "estimated_input_tokens": input_tokens + merge_input_tokens,
            "estimated_output_tokens": estimated_output_tokens + merge_output_tokens,
            "estimated_total_cost": total_cost,
            "input_cost": total_input_cost,
            "output_cost": total_output_cost
        }
        
        print(f"📊 Document Analysis:")
        print(f"   Total tokens: {cost_estimate['total_tokens']:,}")
        print(f"   Chunks needed: {cost_estimate['chunks']}")
        print(f"   Estimated cost: ${cost_estimate['estimated_total_cost']:.4f}")
        print(f"   Input cost: ${cost_estimate['input_cost']:.4f}")
        print(f"   Output cost: ${cost_estimate['output_cost']:.4f}")
        
        if args.estimate_only:
            print("\n✅ Cost estimation complete. Use without --estimate-only to process the document.")
            return
        
        # Initialize summarizer for processing
        summarizer = ChunkedSummarizer(openai_key=args.openai_key)
        
        if not summarizer.client:
            print("❌ OpenAI API key is required. Set OPENAI_API_KEY environment variable or use --openai-key.")
            sys.exit(1)
        
        # Confirm processing
        if cost_estimate['estimated_total_cost'] > 1.0:
            response = input(f"\n⚠️ Estimated cost is ${cost_estimate['estimated_total_cost']:.4f}. Continue? (y/N): ")
            if response.lower() != 'y':
                print("❌ Processing cancelled.")
                return
        
        # Process the document
        print(f"\n🚀 Processing document in {cost_estimate['chunks']} chunks...")
        
        # Summarize the document
        final_summary = summarizer.summarize_text(content, args.max_words)
        
        # Save output
        output_file = args.output or "summary.md"
        save_summary(final_summary, output_file)
        
        # Print final stats
        word_count = len(final_summary.split())
        print(f"\n✅ Summary complete!")
        print(f"   Final word count: {word_count}")
        print(f"   Target: {args.max_words} words")
        print(f"   Output file: {output_file}")
        
        if word_count > args.max_words:
            print(f"⚠️ Warning: Summary exceeds target word count ({word_count} > {args.max_words})")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main() 