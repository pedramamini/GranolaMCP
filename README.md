# GranolaMCP

A Python library for interfacing with Granola.ai meeting data using 100% native Python (no external dependencies).

## Overview

GranolaMCP provides programmatic access to Granola.ai meeting data from JSON cache files, with support for:

- **Core Foundation** (Phase 1) - JSON parsing, timezone conversion, date parsing
- **CLI Tools** (Phase 2) - Command-line interface for data access
- **MCP Server** (Phase 3) - Model Context Protocol server implementation
- **Statistics & Visualization** (Phase 4) - Analytics and ASCII charts

## Features

- 🔍 **JSON Cache Parsing** - Double JSON parsing for Granola cache files
- 🕐 **Timezone Conversion** - UTC to CST conversion using Python's zoneinfo
- 📅 **Flexible Date Parsing** - Support for relative (3d, 24h, 1w) and absolute (YYYY-MM-DD) dates
- 📝 **Meeting & Transcript Models** - Rich data models for meetings and transcripts
- 💻 **CLI Interface** - Full-featured command-line tools for data exploration
- 📊 **Statistics & Analytics** - Comprehensive meeting analytics with ASCII visualizations
- 📈 **ASCII Charts** - Beautiful terminal-friendly charts and graphs
- ⚙️ **Configuration Management** - Simple .env file parsing without dependencies
- 🐍 **Pure Python** - No external dependencies, Python 3.12+ standard library only

## Installation

```bash
# Install from source
git clone https://github.com/pedramamini/granola-mcp.git
cd granola-mcp
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

## CLI Usage

The CLI provides powerful commands for exploring and analyzing meeting data:

### List Meetings
```bash
# List recent meetings
python -m granola_mcp list --last 7d

# List meetings in date range
python -m granola_mcp list --from 2025-01-01 --to 2025-01-31

# Search meetings by title
python -m granola_mcp list --title-contains "standup"

# Filter by participant
python -m granola_mcp list --participant "john@example.com"
```

### Show Meeting Details
```bash
# Show meeting details
python -m granola_mcp show <meeting-id>

# Show meeting with transcript
python -m granola_mcp show <meeting-id> --transcript
```

### Export Meetings
```bash
# Export meeting to markdown
python -m granola_mcp export <meeting-id>

# Save to file
python -m granola_mcp export <meeting-id> > meeting.md
```

### Statistics & Analytics
```bash
# Comprehensive statistics overview
python -m granola_mcp stats --summary

# Meeting frequency analysis
python -m granola_mcp stats --meetings-per-day --last 30d
python -m granola_mcp stats --meetings-per-week --last 12w
python -m granola_mcp stats --meetings-per-month --last 6m

# Duration and participant analysis
python -m granola_mcp stats --duration-distribution
python -m granola_mcp stats --participant-frequency

# Time pattern analysis
python -m granola_mcp stats --time-patterns

# Content analysis
python -m granola_mcp stats --word-analysis

# All statistics with ASCII charts
python -m granola_mcp stats --all
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

## Development Status

- ✅ **Phase 1: Core Foundation** - Complete
  - JSON parsing with double parsing support
  - Timezone conversion (UTC to CST)
  - Date parsing (relative and absolute)
  - Meeting and transcript data models
  - Configuration management

- ✅ **Phase 2: CLI Tools** - Complete
  - Command-line interface with list, show, export commands
  - Beautiful terminal output with colors and tables
  - Advanced filtering and search capabilities
  - Markdown export functionality

- 🚧 **Phase 3: MCP Server** - Planned
  - Model Context Protocol server
  - Real-time data access
  - Integration with AI tools

- ✅ **Phase 4: Statistics & Visualization** - Complete
  - Comprehensive meeting analytics and insights
  - ASCII charts and visualizations (bar charts, histograms, time patterns)
  - Meeting frequency analysis (daily, weekly, monthly)
  - Duration distribution and participant frequency analysis
  - Time pattern analysis (peak hours, busiest days)
  - Content analysis (transcript word counts)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Architecture

See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed architecture documentation.

## Roadmap

See [ROADMAP.md](ROADMAP.md) for development roadmap and future plans.
