# GranolaMCP Implementation Roadmap

## Project Implementation Order

This roadmap outlines the step-by-step implementation plan for the GranolaMCP project, organized by priority and dependencies.

## Phase 1: Core Foundation 🏗️
**Goal**: Establish basic data parsing and models
**Duration**: ~2-3 hours

### 1.1 Project Structure Setup
- [ ] Create directory structure (`granola_mcp/`, `tests/`, `docs/`)
- [ ] Set up `__init__.py` files
- [ ] Create basic `setup.py` for package installation
- [ ] Set up `.env.example` with cache file path

### 1.2 Core Utilities (`utils/`)
- [ ] `config.py` - Simple .env file parsing (no dependencies)
- [ ] `date_parser.py` - Native relative/absolute date parsing
  - Parse `3d`, `24h`, `1w` format using `datetime.timedelta`
  - Parse `YYYY-MM-DD` format using `datetime.strptime`
  - Date range validation and error handling

### 1.3 Timezone Handling (`core/timezone_utils.py`)
- [ ] UTC to CST conversion using `zoneinfo` (Python 3.9+)
- [ ] Timestamp parsing from ISO 8601 format
- [ ] Timezone-aware datetime utilities

### 1.4 JSON Parser (`core/parser.py`)
- [ ] `GranolaParser` class for loading cache file
- [ ] Double JSON parsing logic (`json.loads(json.loads(data)['cache'])`)
- [ ] Error handling for malformed JSON
- [ ] Basic validation of expected structure

**Deliverable**: Core utilities that can load and parse the JSON cache file

---

## Phase 2: Data Models 📊
**Goal**: Rich data models for meetings and transcripts
**Duration**: ~3-4 hours

### 2.1 Transcript Processing (`core/transcript.py`)
- [ ] `TranscriptSegment` class for individual segments
- [ ] Transcript stitching algorithm:
  - Sort segments by timestamp
  - Group by source (microphone/system)
  - Combine consecutive segments
  - Handle overlapping timestamps
- [ ] Full transcript generation with speaker identification

### 2.2 Meeting Model (`core/meeting.py`)
- [ ] `Meeting` class with rich metadata
- [ ] Properties for:
  - Basic info (id, title, created_at, updated_at)
  - Participants (creator, attendees)
  - Content (notes_plain, notes_markdown, summary)
  - Stitched full transcript
  - Duration calculation
- [ ] Timezone conversion for all timestamps
- [ ] Lazy loading of transcript data

### 2.3 Data Access Layer (`core/parser.py` extensions)
- [ ] Meeting filtering by date range
- [ ] Meeting search by title/content
- [ ] Participant-based queries
- [ ] Statistics generation methods

**Deliverable**: Rich Meeting objects with stitched transcripts and metadata

---

## Phase 3: CLI Interface 🖥️
**Goal**: Beautiful command-line interface
**Duration**: ~4-5 hours

### 3.1 CLI Foundation (`cli/`)
- [ ] `main.py` with `argparse` setup
- [ ] Subcommand structure (list, show, export, stats)
- [ ] Global options (--config, --cache-path, --timezone)
- [ ] Error handling and user-friendly messages

### 3.2 Output Formatting (`cli/formatters/`)
- [ ] `colors.py` - ANSI escape codes and color utilities
- [ ] `table.py` - ASCII table formatting with borders
- [ ] `charts.py` - ASCII bar charts and histograms
- [ ] `markdown.py` - Clean markdown export formatting

### 3.3 List Command (`cli/commands/list.py`)
- [ ] Meeting list with filters:
  - `--last 3d/24h/1w` (relative dates)
  - `--from YYYY-MM-DD --to YYYY-MM-DD` (absolute dates)
  - `--title-contains TEXT`
  - `--participant EMAIL`
- [ ] Colored table output with:
  - Meeting ID (truncated)
  - Title
  - Date/Time (CST)
  - Duration
  - Participant count

### 3.4 Show Command (`cli/commands/show.py`)
- [ ] Full meeting details display
- [ ] Options: `--transcript`, `--notes`, `--metadata`
- [ ] Formatted output with colors and sections
- [ ] Transcript with speaker identification

### 3.5 Export Command (`cli/commands/export.py`)
- [ ] Markdown export to STDOUT
- [ ] Include: metadata, participants, notes, full transcript
- [ ] Clean formatting suitable for documentation

**Deliverable**: Fully functional CLI with list, show, and export commands

---

## Phase 4: Statistics & Visualization 📈
**Goal**: Meeting analytics and ASCII charts
**Duration**: ~2-3 hours

### 4.1 Statistics Engine (`cli/commands/stats.py`)
- [ ] Meeting frequency analysis
- [ ] Duration distribution calculation
- [ ] Participant frequency tracking
- [ ] Date range analysis

### 4.2 ASCII Visualization (`cli/formatters/charts.py`)
- [ ] Bar chart for meetings per day/week/month
- [ ] Histogram for meeting duration distribution
- [ ] Simple line graph for trends
- [ ] Participant frequency chart

### 4.3 Statistics Commands
- [ ] `stats --meetings-per-day --last 30d`
- [ ] `stats --duration-distribution`
- [ ] `stats --participant-frequency`
- [ ] `stats --summary` (overall statistics)

**Deliverable**: Rich statistics and beautiful ASCII visualizations

---

## Phase 5: MCP Interface 🤖
**Goal**: STDIO MCP server for LLM integration
**Duration**: ~3-4 hours

### 5.1 MCP Server Foundation (`mcp/server.py`)
- [ ] JSON-RPC STDIO server implementation
- [ ] MCP protocol compliance
- [ ] Tool registration and discovery
- [ ] Error handling and logging

### 5.2 MCP Tools (`mcp/tools.py`)
- [ ] `search_meetings` - Search with various filters
- [ ] `get_transcript` - Get full transcript for meeting ID
- [ ] `get_meeting_notes` - Get structured notes and metadata
- [ ] `get_statistics` - Generate meeting statistics
- [ ] `list_participants` - List all participants
- [ ] `export_markdown` - Export meeting in markdown format

### 5.3 MCP Integration
- [ ] Tool input validation and schemas
- [ ] Response formatting for LLM consumption
- [ ] Comprehensive error handling
- [ ] Performance optimization for large datasets

**Deliverable**: Full MCP server with all planned tools

---

## Phase 6: Testing & Documentation 🧪
**Goal**: Comprehensive testing and documentation
**Duration**: ~2-3 hours

### 6.1 Unit Tests (`tests/`)
- [ ] `test_parser.py` - JSON parsing and data loading
- [ ] `test_meeting.py` - Meeting model and transcript stitching
- [ ] `test_cli.py` - CLI command functionality
- [ ] `test_mcp.py` - MCP server and tools

### 6.2 Integration Tests
- [ ] End-to-end CLI workflows
- [ ] MCP server integration
- [ ] Large dataset performance testing

### 6.3 Documentation
- [ ] `CLI-USAGE.md` - Comprehensive CLI examples
- [ ] `MCP-INTERFACE.md` - MCP tool documentation
- [ ] Update `README.md` with installation and usage
- [ ] Code documentation and docstrings

**Deliverable**: Well-tested, documented, production-ready package

---

## Implementation Priority

### Critical Path (MVP)
1. **Phase 1** → **Phase 2** → **Phase 3.1-3.4** (Core CLI)
2. This gives you a working CLI tool for exploring meetings

### Extended Features
3. **Phase 4** (Statistics) - Adds analytics capabilities
4. **Phase 5** (MCP) - Enables LLM integration
5. **Phase 6** (Testing) - Production readiness

### Quick Start Option
For rapid prototyping, you could implement:
1. Basic JSON parser (`core/parser.py`)
2. Simple Meeting model (`core/meeting.py`)
3. Basic list command (`cli/commands/list.py`)

This would give you a working tool in ~2 hours.

## Development Commands

```bash
# Development setup
cd GranolaMCP
python -m granola_mcp --help

# Testing during development
python -m granola_mcp list --last 7d
python -m granola_mcp show <meeting-id>
python -m granola_mcp export <meeting-id>

# MCP server testing
python -m granola_mcp.mcp.server
```

## Success Criteria

### Phase 1-3 (MVP)
- [ ] Can list meetings with date filters
- [ ] Can show full meeting details with stitched transcript
- [ ] Can export meetings to markdown
- [ ] Beautiful terminal output with colors

### Phase 4-5 (Full Feature)
- [ ] Rich statistics with ASCII charts
- [ ] Working MCP server with all tools
- [ ] LLM can query and analyze meeting data

### Phase 6 (Production)
- [ ] Comprehensive test coverage
- [ ] Complete documentation
- [ ] Performance optimized for large datasets
- [ ] Error handling for edge cases

This roadmap provides a clear path from basic functionality to a full-featured meeting data interface, with natural stopping points for testing and validation along the way.