# GranolaMCP MCP Server Usage Guide

This guide provides comprehensive instructions for manually running the GranolaMCP MCP (Model Context Protocol) server, configuring it, testing it, and integrating it with LLM systems.

## Table of Contents

1. [Basic MCP Server Startup](#basic-mcp-server-startup)
2. [Configuration Setup](#configuration-setup)
3. [Testing the MCP Server](#testing-the-mcp-server)
4. [Integration with LLM Systems](#integration-with-llm-systems)
5. [Available MCP Tools](#available-mcp-tools)
6. [Troubleshooting](#troubleshooting)

## Basic MCP Server Startup

### Prerequisites

- Python 3.12 or higher
- GranolaMCP installed (`pip install -e .` from the project root)
- Access to a Granola cache file (typically located at `~/Library/Application Support/Granola/cache-v3.json` on macOS)

### Starting the Server

The MCP server can be started using Python's module execution:

```bash
# Basic startup with default configuration
python -m granola_mcp.mcp

# Using a specific Python interpreter
/Users/pedram/venv3-20241001/bin/python -m granola_mcp.mcp
```

### Command-Line Options

The MCP server supports several command-line options:

```bash
# Show help and available options
python -m granola_mcp.mcp --help

# Start with debug logging enabled
python -m granola_mcp.mcp --debug

# Specify a custom cache file path
python -m granola_mcp.mcp --cache-path "/path/to/your/cache.json"

# Show version information
python -m granola_mcp.mcp --version

# Combine options
python -m granola_mcp.mcp --debug --cache-path "/custom/path/cache.json"
```

### Server Communication

The MCP server communicates via **STDIO** using **JSON-RPC 2.0** protocol. This means:

- Input is received from `stdin`
- Output is sent to `stdout`
- Debug/error messages go to `stderr` (when `--debug` is enabled)
- The server runs continuously until interrupted (Ctrl+C)

## Configuration Setup

### Environment Variables

The server can be configured using environment variables or a `.env` file:

```bash
# Set cache path
export GRANOLA_CACHE_PATH="/Users/pedram/Library/Application Support/Granola/cache-v3.json"

# Set timezone (optional)
export GRANOLA_TIMEZONE="America/Chicago"

# Enable debug mode (optional)
export GRANOLA_DEBUG="true"

# Set custom date format (optional)
export GRANOLA_DATE_FORMAT="%Y-%m-%d %H:%M:%S %Z"
```

### .env File Setup

1. **Copy the example file:**
   ```bash
   cp .env.example .env
   ```

2. **Edit the .env file:**
   ```bash
   # GranolaMCP Configuration
   # Copy this file to .env and update the values as needed

   # Path to the Granola cache file
   # Default: /Users/pedram/Library/Application Support/Granola/cache-v3.json
   GRANOLA_CACHE_PATH=/Users/pedram/Library/Application Support/Granola/cache-v3.json

   # Optional: Set timezone (default is America/Chicago for CST)
   # GRANOLA_TIMEZONE=America/Chicago

   # Optional: Enable debug logging
   # GRANOLA_DEBUG=true

   # Optional: Set custom date format for output
   # GRANOLA_DATE_FORMAT=%Y-%m-%d %H:%M:%S %Z
   ```

### Cache File Path Configuration

The server looks for the Granola cache file in this order:

1. Command-line argument: `--cache-path`
2. Environment variable: `GRANOLA_CACHE_PATH`
3. `.env` file: `GRANOLA_CACHE_PATH`
4. Default location: `~/Library/Application Support/Granola/cache-v3.json`

**Finding your cache file:**
```bash
# Common locations on macOS
ls -la ~/Library/Application\ Support/Granola/
ls -la ~/Library/Application\ Support/Granola/cache-v3.json

# Check if the file exists and is readable
python -c "
import os
cache_path = os.path.expanduser('~/Library/Application Support/Granola/cache-v3.json')
print(f'Cache file exists: {os.path.exists(cache_path)}')
print(f'Cache file readable: {os.access(cache_path, os.R_OK) if os.path.exists(cache_path) else False}')
print(f'Cache file size: {os.path.getsize(cache_path) if os.path.exists(cache_path) else 0} bytes')
"
```

## Testing the MCP Server

### Manual Testing with JSON-RPC

You can test the MCP server manually by sending JSON-RPC requests via stdin:

1. **Start the server in debug mode:**
   ```bash
   python -m granola_mcp.mcp --debug
   ```

2. **Send initialization request:**
   ```json
   {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "test-client", "version": "1.0.0"}}}
   ```

3. **List available tools:**
   ```json
   {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}
   ```

4. **Test a tool (search meetings):**
   ```json
   {"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {"name": "search_meetings", "arguments": {"limit": 5}}}
   ```

5. **Test ping:**
   ```json
   {"jsonrpc": "2.0", "id": 4, "method": "ping", "params": {}}
   ```

### Quick Verification

Use the included verification script to quickly test the server:

```bash
# Quick verification
python verify_mcp_server.py

# With custom cache path
python verify_mcp_server.py --cache-path "/path/to/cache.json"
```

**Expected output:**
```
🔍 Verifying GranolaMCP MCP Server...
✅ MCP Server initialized successfully
   Server: granola-mcp v1.0.0
   Available tools: 9
   Tools: list_meetings, search_meetings, get_meeting, get_transcript, get_meeting_notes, list_participants, get_statistics, export_meeting, analyze_patterns

🎉 Verification successful! The MCP server is ready for use.

✅ Verification completed successfully!
```

### Automated Testing Script

For more comprehensive testing, use the included test script:

```bash
# Run comprehensive tests
python test_mcp_server.py

# With custom cache path and timeout
python test_mcp_server.py --cache-path "/path/to/cache.json" --timeout 10
```

## Integration with LLM Systems

### Claude Desktop Integration

To integrate with Claude Desktop, add the server configuration to your Claude Desktop config file:

**Location:** `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "granola-mcp": {
      "command": "/Users/pedram/venv3-20241001/bin/python",
      "args": ["-m", "granola_mcp.mcp"],
      "env": {
        "GRANOLA_CACHE_PATH": "/Users/pedram/Library/Application Support/Granola/cache-v3.json"
      }
    }
  }
}
```

**With debug mode:**
```json
{
  "mcpServers": {
    "granola-mcp": {
      "command": "/Users/pedram/venv3-20241001/bin/python",
      "args": ["-m", "granola_mcp.mcp", "--debug"],
      "env": {
        "GRANOLA_CACHE_PATH": "/Users/pedram/Library/Application Support/Granola/cache-v3.json"
      }
    }
  }
}
```

### Other MCP Clients

For other MCP-compatible clients, use these connection parameters:

- **Protocol:** STDIO
- **Command:** `python -m granola_mcp.mcp`
- **Working Directory:** Path to GranolaMCP installation
- **Environment Variables:** Set `GRANOLA_CACHE_PATH` as needed

### Custom Integration

For custom integrations, you can spawn the MCP server as a subprocess:

```python
import subprocess
import json

# Start the MCP server
process = subprocess.Popen(
    ["python", "-m", "granola_mcp.mcp"],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
    env={"GRANOLA_CACHE_PATH": "/path/to/cache.json"}
)

# Send initialization
init_request = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
        "protocolVersion": "2024-11-05",
        "capabilities": {},
        "clientInfo": {"name": "my-client", "version": "1.0.0"}
    }
}

process.stdin.write(json.dumps(init_request) + "\n")
process.stdin.flush()

# Read response
response = json.loads(process.stdout.readline())
print("Server initialized:", response)
```

## Available MCP Tools

The GranolaMCP server provides 9 comprehensive tools for accessing meeting data:

### 1. list_meetings
List recent meetings with optional date range filters. **Defaults to last 3 days** if no date filters are specified. This is the primary tool for getting a simple list of meetings.

**Parameters:**
- `from_date` (optional): Start date (ISO format or relative like '30d', '1w', '3d'). Defaults to '3d' if no date filters specified
- `to_date` (optional): End date (ISO format or relative like '1d') 
- `limit` (optional): Maximum number of results

**Examples:**
```json
{
  "name": "list_meetings",
  "arguments": {
    "limit": 10
  }
}
```

```json
{
  "name": "list_meetings",
  "arguments": {
    "from_date": "1w",
    "limit": 5
  }
}
```

### 2. search_meetings
Search meetings with flexible filters including text search and participant filters. **Defaults to last 3 days** if no date filters are specified.

**Parameters:**
- `query` (optional): Text search in title/content
- `from_date` (optional): Start date (ISO format or relative like '30d'). Defaults to '3d' if no date filters specified
- `to_date` (optional): End date (ISO format or relative like '1d')
- `participant` (optional): Filter by participant email/name
- `limit` (optional): Maximum number of results

**Examples:**
```json
{
  "name": "search_meetings",
  "arguments": {
    "query": "project review",
    "from_date": "7d",
    "limit": 10
  }
}
```

```json
{
  "name": "search_meetings",
  "arguments": {
    "limit": 5
  }
}
```
*Note: This will search the last 3 days by default*

### 3. get_meeting
Get complete meeting details including metadata and transcript info.

**Parameters:**
- `meeting_id` (required): Meeting ID to retrieve

**Example:**
```json
{
  "name": "get_meeting",
  "arguments": {
    "meeting_id": "meeting-123"
  }
}
```

### 4. get_transcript
Get full transcript for a specific meeting.

**Parameters:**
- `meeting_id` (required): Meeting ID
- `include_speakers` (optional): Include speaker identification (default: true)
- `include_timestamps` (optional): Include timestamps (default: false)

**Example:**
```json
{
  "name": "get_transcript",
  "arguments": {
    "meeting_id": "meeting-123",
    "include_speakers": true,
    "include_timestamps": true
  }
}
```

### 5. get_meeting_notes
Get structured notes and summary for a meeting.

**Parameters:**
- `meeting_id` (required): Meeting ID

### 6. list_participants
List all participants with frequency data and meeting history.

**Parameters:**
- `from_date` (optional): Start date filter
- `to_date` (optional): End date filter
- `min_meetings` (optional): Minimum meeting count filter

### 7. get_statistics
Generate meeting statistics and analytics.

**Parameters:**
- `stat_type` (required): Type of statistics
  - `"summary"`: Overall summary statistics
  - `"frequency"`: Meeting frequency analysis
  - `"duration"`: Duration statistics and distribution
  - `"participants"`: Participant statistics
  - `"patterns"`: Time pattern analysis
- `from_date` (optional): Start date filter
- `to_date` (optional): End date filter

### 8. export_meeting
Export meeting in markdown format.

**Parameters:**
- `meeting_id` (required): Meeting ID to export
- `include_transcript` (optional): Include full transcript (default: true)
- `include_metadata` (optional): Include meeting metadata (default: true)

### 9. analyze_patterns
Analyze meeting patterns and trends.

**Parameters:**
- `pattern_type` (required): Type of pattern analysis
  - `"time"`: Time-based patterns (hourly, daily)
  - `"frequency"`: Frequency patterns (daily, weekly, monthly)
  - `"participants"`: Participant collaboration patterns
  - `"duration"`: Duration trend analysis
- `from_date` (optional): Start date filter
- `to_date` (optional): End date filter

## Troubleshooting

### Common Issues and Solutions

#### 1. Cache File Not Found

**Error:** `Failed to initialize server: Invalid cache file structure`

**Solutions:**
- Verify the cache file path: `ls -la ~/Library/Application\ Support/Granola/cache-v3.json`
- Check if Granola app is installed and has created meetings
- Ensure the cache file is readable: `chmod 644 ~/Library/Application\ Support/Granola/cache-v3.json`
- Try specifying the path explicitly: `--cache-path "/full/path/to/cache.json"`

#### 2. Permission Denied

**Error:** `Permission denied` when accessing cache file

**Solutions:**
```bash
# Check file permissions
ls -la ~/Library/Application\ Support/Granola/cache-v3.json

# Fix permissions if needed
chmod 644 ~/Library/Application\ Support/Granola/cache-v3.json

# Check directory permissions
ls -la ~/Library/Application\ Support/Granola/
```

#### 3. Python Module Not Found

**Error:** `No module named 'granola_mcp'`

**Solutions:**
```bash
# Install in development mode
pip install -e .

# Or install from PyPI (when available)
pip install granola-mcp

# Verify installation
python -c "import granola_mcp; print(granola_mcp.__version__)"
```

#### 4. JSON-RPC Communication Issues

**Error:** Server not responding to requests

**Solutions:**
- Enable debug mode: `--debug`
- Check that requests are properly formatted JSON-RPC 2.0
- Ensure each request is on a single line
- Verify the server is initialized before calling tools
- Check stderr for error messages

#### 5. Empty or Invalid Cache File

**Error:** `Invalid cache file structure` or no meetings found

**Solutions:**
```bash
# Check cache file content
head -n 20 ~/Library/Application\ Support/Granola/cache-v3.json

# Verify JSON structure
python -c "
import json
with open('/Users/pedram/Library/Application Support/Granola/cache-v3.json') as f:
    data = json.load(f)
    print(f'Cache contains {len(data.get(\"meetings\", []))} meetings')
"

# If cache is empty, ensure Granola app has recorded meetings
```

### Debug Mode Usage

Enable debug mode for detailed logging:

```bash
# Start with debug logging
python -m granola_mcp.mcp --debug

# Debug output goes to stderr, so you can redirect it
python -m granola_mcp.mcp --debug 2> debug.log

# Or view debug output while using the server
python -m granola_mcp.mcp --debug 2>&1 | tee debug.log
```

**Debug output includes:**
- Server startup messages
- Request/response logging
- Cache file validation
- Tool execution details
- Error stack traces

### Log Interpretation

**Successful startup:**
```
INFO - Starting MCP server...
INFO - MCP server initialized successfully
```

**Cache file issues:**
```
ERROR - Initialization error: Invalid cache file structure
ERROR - Failed to load meetings: [Errno 2] No such file or directory
```

**Tool execution:**
```
DEBUG - Received request: {"jsonrpc": "2.0", "id": 1, "method": "tools/call", ...}
DEBUG - Sent response: {"jsonrpc": "2.0", "id": 1, "result": {...}}
```

### Performance Considerations

- **Large cache files:** The server loads all meetings into memory on initialization
- **Concurrent requests:** The server processes requests sequentially
- **Memory usage:** Proportional to the size of your meeting data
- **Startup time:** May take a few seconds with large cache files

### Getting Help

If you encounter issues not covered here:

1. **Check the logs:** Always run with `--debug` first
2. **Verify your setup:** Ensure cache file exists and is readable
3. **Test with minimal data:** Try with a small cache file first
4. **Check the GitHub issues:** [https://github.com/pedramamini/granola-mcp/issues](https://github.com/pedramamini/granola-mcp/issues)

---

## Quick Reference

### Start Server
```bash
python -m granola_mcp.mcp --debug
```

### Quick Verification
```bash
python verify_mcp_server.py
```

### Basic Test
```json
{"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "test", "version": "1.0"}}}
{"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}
{"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {"name": "search_meetings", "arguments": {"limit": 5}}}
```

### Default Behavior
- **search_meetings** defaults to last 3 days if no date filters specified
- All other tools search the entire cache unless filtered

### Claude Desktop Config
```json
{
  "mcpServers": {
    "granola-mcp": {
      "command": "/Users/pedram/venv3-20241001/bin/python",
      "args": ["-m", "granola_mcp.mcp"],
      "env": {
        "GRANOLA_CACHE_PATH": "/Users/pedram/Library/Application Support/Granola/cache-v3.json"
      }
    }
  }
}