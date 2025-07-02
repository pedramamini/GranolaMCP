"""
MCP server entry point for GranolaMCP.

Provides the main entry point for running the MCP STDIO server.
"""

import sys
import argparse
from .server import MCPServer


def main():
    """Main entry point for the MCP server."""
    parser = argparse.ArgumentParser(
        description="Granola MCP Server - Expose Granola.ai meeting data via MCP protocol",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m granola_mcp.mcp                    # Start server with default cache
  python -m granola_mcp.mcp --debug            # Start with debug logging
  python -m granola_mcp.mcp --cache-path /path/to/cache.json  # Custom cache path

The server communicates via STDIO using JSON-RPC 2.0 following the MCP protocol.
        """
    )

    parser.add_argument(
        "--cache-path",
        type=str,
        help="Path to Granola cache file (default: uses config)"
    )

    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging to stderr"
    )

    parser.add_argument(
        "--version",
        action="version",
        version="GranolaMCP 1.0.0"
    )

    args = parser.parse_args()

    try:
        server = MCPServer(
            cache_path=args.cache_path,
            debug=args.debug
        )

        server.run()

    except KeyboardInterrupt:
        if args.debug:
            print("Server interrupted by user", file=sys.stderr)
        sys.exit(0)
    except Exception as e:
        print(f"Server error: {e}", file=sys.stderr)
        if args.debug:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()