# GranolaMCP

A comprehensive Python library and CLI tool for accessing and analyzing Granola.ai meeting data, featuring a complete MCP (Model Context Protocol) server for AI integration.

## 📋 Changelog

### 2025-07-04 - New Collect Command 🎯
- **NEW**: Added `granola collect` command for exporting your own words from meetings
- **FEATURE**: Automatically filters microphone audio (your spoken words) vs system audio (what you heard)
- **FEATURE**: Organizes exported text by day into `YYYY-MM-DD.txt` files
- **FEATURE**: Supports flexible date ranges (`--last 7d`, `--from/--to`)
- **FEATURE**: Optional timestamps and meeting metadata inclusion
- **FEATURE**: Minimum word filtering to exclude short utterances
- **USE CASE**: Perfect for creating LLM training datasets from your own speech

## Overview

GranolaMCP provides complete access to Granola.ai meeting data through multiple interfaces:

- **📚 Python Library** - Programmatic access to meetings, transcripts, and summaries
- **💻 Command Line Interface** - Rich CLI with advanced filtering and analytics
- **🤖 MCP Server** - Model Context Protocol server for AI integration (Claude, etc.)
- **📊 Analytics & Visualization** - Comprehensive statistics with ASCII charts

## Data Source

**GranolaMCP operates entirely on local cache files** - it reads meeting data directly from Granola's local cache file (`cache-v3.json`) without making any API calls to Granola's servers. This approach provides:

- **🔌 No Network Dependency** - Works completely offline
- **⚡ Fast Access** - Direct file system access with no API rate limits  
- **🔒 Privacy Focused** - Your meeting data never leaves your machine
- **🛡️ No Authentication** - No need to manage API keys or tokens

**Alternative Approach Available:** While not implemented in this library, it's technically possible to extract access tokens from Granola's `supabase.json` configuration file and communicate directly with the Granola API. However, the cache-based approach provides better performance, privacy, and reliability for most use cases.

## ✨ Key Features

### Core Data Access
- 🔍 **Smart JSON Parsing** - Handles Granola's complex double-JSON cache structure
- 📝 **AI Summary Extraction** - Separates AI-generated summaries from human notes
- 💬 **Full Transcript Access** - Complete speaker-identified transcripts with timing
- 📁 **Folder Organization** - Meeting organization by folders (OPSWAT, Mozilla, Personal, etc.)
- 🕐 **Accurate Duration Calculation** - Real meeting duration from transcript timing
- 🏷️ **Rich Metadata** - Participants, timestamps, and meeting context

### Advanced CLI Interface
- 🎯 **Intelligent Filtering** - Filter by date, participant, title, or folder
- 📊 **Table Display** - Clean tables showing transcript/summary word counts
- 🔍 **Smart Search** - Search across titles, content, and participants
- 📈 **Analytics Dashboard** - Meeting frequency, duration patterns, and trends
- 🎨 **Beautiful Output** - Color-coded, formatted terminal displays
- 📄 **Export Capabilities** - Export to markdown with full formatting

### MCP Server for AI Integration
- 🤖 **8 Comprehensive Tools** - Complete meeting data access for AI assistants
- 🔌 **Claude Desktop Integration** - Ready-to-use configuration for Claude
- 📡 **JSON-RPC Protocol** - Standard MCP protocol implementation
- ⚡ **Real-time Access** - Live access to your latest meeting data
- 🛡️ **Robust Error Handling** - Graceful handling of missing data and errors

### Enterprise-Ready Features
- 🐍 **Zero Dependencies** - Pure Python standard library only
- ⚙️ **Flexible Configuration** - Environment variables, .env files, CLI arguments
- 🕐 **Timezone Aware** - Proper UTC to local timezone conversion
- 📅 **Flexible Date Parsing** - Relative (3d, 24h, 1w) and absolute dates
- 🎯 **Production Ready** - Comprehensive error handling and logging

## Installation

```bash
# Install from source
git clone https://github.com/pedramamini/GranolaMCP.git
cd GranolaMCP
pip install -e .

# Or install from PyPI (when available)
pip install granola-mcp
```

## Quick Start

### 1. Configuration

Copy the example configuration file and update the cache path:

```bash
cp .env.example .env
```

Edit `.env` to set your Granola cache file path:

```env
GRANOLA_CACHE_PATH=/Users/pedram/Library/Application Support/Granola/cache-v3.json
```

### 2. Basic Usage

```python
from granola_mcp import GranolaParser
from granola_mcp.utils.date_parser import parse_date
from granola_mcp.core.timezone_utils import convert_utc_to_cst

# Initialize parser
parser = GranolaParser()

# Load and parse cache
cache_data = parser.load_cache()
meetings = parser.get_meetings()

print(f"Found {len(meetings)} meetings")

# Work with individual meetings
from granola_mcp.core.meeting import Meeting

for meeting_data in meetings[:5]:  # First 5 meetings
    meeting = Meeting(meeting_data)
    print(f"Meeting: {meeting.title}")
    print(f"Start: {meeting.start_time}")
    print(f"Participants: {', '.join(meeting.participants)}")

    if meeting.has_transcript():
        transcript = meeting.transcript
        print(f"Transcript: {transcript.word_count} words")
    print("---")
```

### 3. Date Parsing Examples

```python
from granola_mcp.utils.date_parser import parse_date, get_date_range

# Parse relative dates
three_days_ago = parse_date("3d")      # 3 days ago
last_week = parse_date("1w")           # 1 week ago
yesterday = parse_date("24h")          # 24 hours ago

# Parse absolute dates
specific_date = parse_date("2025-01-01")
specific_datetime = parse_date("2025-01-01 14:30:00")

# Get date ranges
start_date, end_date = get_date_range("1w", "1d")  # From 1 week ago to 1 day ago
```

### 4. Timezone Conversion

```python
from granola_mcp.core.timezone_utils import convert_utc_to_cst
import datetime

# Convert UTC timestamp to CST
utc_time = datetime.datetime.now(datetime.timezone.utc)
cst_time = convert_utc_to_cst(utc_time)

print(f"UTC: {utc_time}")
print(f"CST: {cst_time}")
```

## 💻 CLI Usage

The CLI provides powerful commands for exploring and analyzing meeting data with advanced features:

### List Meetings with Rich Display
```bash
# List recent meetings with word counts and folders
python -m granola_mcp list --last 7d

# Filter by folder (OPSWAT, Mozilla, Personal, etc.)
python -m granola_mcp list --folder Mozilla --limit 10

# Search meetings by title
python -m granola_mcp list --title-contains "standup" --folder OPSWAT

# Filter by participant and date range
python -m granola_mcp list --participant "john@example.com" --from 30d

# Sort by different criteria
python -m granola_mcp list --sort-by duration --reverse --limit 10
```

**Table Output Features:**
- Meeting ID (shortened for readability)
- Title with smart truncation
- Date and time in local timezone
- **Accurate duration** from transcript timing
- **Transcript word count** (6.0k format for large numbers)
- **AI Summary word count** (from extracted summaries)
- **Folder organization** (Mozilla, OPSWAT, Personal, etc.)

### Show Meeting Details
```bash
# Show meeting overview with availability indicators
python -m granola_mcp show <meeting-id>

# Show AI-generated summary (structured content)
python -m granola_mcp show <meeting-id> --summary

# Show human notes/transcript content
python -m granola_mcp show <meeting-id> --notes

# Show full transcript with speakers
python -m granola_mcp show <meeting-id> --transcript

# Show everything including metadata
python -m granola_mcp show <meeting-id> --all
```

**Meeting Display Features:**
- Clear availability indicators (AI Summary: Available/Not available)
- Separated AI summaries vs human notes
- Full speaker-identified transcripts
- Rich metadata with proper timezone conversion
- Participant lists and tags

### Export Meetings
```bash
# Export meeting to markdown with full formatting
python -m granola_mcp export <meeting-id>

# Export without transcript for summaries only
python -m granola_mcp export <meeting-id> --no-transcript

# Save to file with proper formatting
python -m granola_mcp export <meeting-id> > meeting.md
```

### Statistics & Analytics Dashboard
```bash
# Comprehensive overview with meeting statistics
python -m granola_mcp stats --summary

# Meeting frequency analysis with ASCII charts
python -m granola_mcp stats --meetings-per-day --last 30d
python -m granola_mcp stats --meetings-per-week --last 12w
python -m granola_mcp stats --meetings-per-month --last 6m

# Duration analysis (only for meetings with transcripts)
python -m granola_mcp stats --duration-distribution

# Participant collaboration patterns
python -m granola_mcp stats --participant-frequency

# Time pattern analysis (peak hours, busiest days)
python -m granola_mcp stats --time-patterns

# Content analysis with word counts
python -m granola_mcp stats --word-analysis

# Complete analytics dashboard
python -m granola_mcp stats --all
```

### Collect Your Own Words for LLM Training
```bash
# Collect your own words from last 7 days
granola collect --last 7d --output-dir ./my-words

# Collect from specific date range
granola collect --from 2025-01-01 --to 2025-01-31 --output-dir ./january-words

# Include timestamps and meeting metadata
granola collect --last 30d --output-dir ./my-words --include-timestamps --include-meeting-info

# Filter out very short utterances (minimum 3 words)
granola collect --last 30d --output-dir ./my-words --min-words 3

# Collect all available data
granola collect --last 2y --output-dir ./complete-dataset --min-words 1
```

**Key Features:**
- **Speaker Separation**: Automatically filters your words (microphone source) from what you heard (system source)
- **Daily Organization**: Creates separate `YYYY-MM-DD.txt` files for each day
- **LLM Ready**: Perfect format for creating training datasets from your own speech
- **Flexible Filtering**: Date ranges, minimum word counts, optional metadata
- **File Management**: Safely overwrites existing files with identical content

## 🤖 MCP Server for AI Integration

Start the MCP server to integrate with AI assistants like Claude Desktop:

```bash
# Start MCP server
python -m granola_mcp.mcp

# Start with debug logging
python -m granola_mcp.mcp --debug

# Start with custom cache path
python -m granola_mcp.mcp --cache-path "/path/to/cache.json"
```

### Claude Desktop Integration

Add to your `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "granola-mcp": {
      "command": "python",
      "args": ["-m", "granola_mcp.mcp"],
      "env": {
        "GRANOLA_CACHE_PATH": "/Users/[username]/Library/Application Support/Granola/cache-v3.json"
      }
    }
  }
}
```

### Available MCP Tools

The server provides 10 comprehensive tools:

1. **get_recent_meetings** - Get the most recent X meetings (goes back as far as needed)
2. **list_meetings** - Simple meeting list with date filters (defaults to last 3 days)
3. **search_meetings** - Advanced search with text, participant, and date filters
4. **get_meeting** - Complete meeting details with metadata
5. **get_transcript** - Full transcript with speaker identification
6. **get_meeting_notes** - Structured AI summaries and human notes
7. **list_participants** - Participant analysis with meeting history
8. **get_statistics** - Generate analytics (summary, frequency, duration, patterns)
9. **export_meeting** - Export meetings in markdown format
10. **analyze_patterns** - Analyze meeting patterns and trends

### MCP Usage Examples

```json
// Get the 5 most recent meetings (regardless of date)
{
  "name": "get_recent_meetings",
  "arguments": {
    "count": 5
  }
}

// List recent meetings (last 3 days by default)  
{
  "name": "list_meetings",
  "arguments": {
    "limit": 10
  }
}

// List meetings from last week
{
  "name": "list_meetings", 
  "arguments": {
    "from_date": "7d",
    "limit": 5
  }
}

// Search meetings with text query
{
  "name": "search_meetings",
  "arguments": {
    "query": "project review",
    "from_date": "7d"
  }
}

// Get complete meeting details
{
  "name": "get_meeting",
  "arguments": {
    "meeting_id": "f47f8acd-70bd-49b7-8b0d-83c49eee07d1"
  }
}

// Get meeting statistics
{
  "name": "get_statistics",
  "arguments": {
    "stat_type": "summary"
  }
}
```

## Project Structure

```
granola_mcp/
├── __init__.py              # Main package exports
├── core/                    # Core functionality
│   ├── __init__.py
│   ├── parser.py           # JSON cache parser
│   ├── meeting.py          # Meeting data model
│   ├── transcript.py       # Transcript data model
│   └── timezone_utils.py   # UTC to CST conversion
├── utils/                   # Utility functions
│   ├── __init__.py
│   ├── config.py           # Configuration management
│   └── date_parser.py      # Date parsing utilities
├── cli/                     # CLI tools (Phase 2 & 4)
│   ├── __init__.py
│   ├── main.py             # Main CLI entry point
│   ├── commands/           # CLI commands
│   │   ├── list.py         # List meetings
│   │   ├── show.py         # Show meeting details
│   │   ├── export.py       # Export meetings
│   │   └── stats.py        # Statistics & analytics
│   └── formatters/         # Output formatters
│       ├── colors.py       # ANSI color utilities
│       ├── table.py        # Table formatting
│       ├── markdown.py     # Markdown export
│       └── charts.py       # ASCII charts & visualizations
└── mcp/                     # MCP server (Phase 3)
    └── __init__.py
```

## Requirements

- Python 3.12 or higher
- No external dependencies (uses only Python standard library)

## License

MIT License - see LICENSE file for details.

## Architecture

See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed architecture documentation.

## Roadmap

See [ROADMAP.md](ROADMAP.md) for development roadmap and future plans.
