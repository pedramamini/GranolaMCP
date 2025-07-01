"""
MCP (Model Context Protocol) STDIO server implementation for GranolaMCP.

Provides a JSON-RPC STDIO server that exposes meeting data and analytics
to LLM systems following the MCP protocol specification.
"""

import json
import sys
import logging
import traceback
from typing import Dict, Any, List, Optional, Union
from ..core.parser import GranolaParser, GranolaParseError
from .tools import MCPTools


class MCPServer:
    """
    MCP STDIO server for exposing Granola meeting data to LLMs.

    Implements the Model Context Protocol over STDIO using JSON-RPC 2.0
    for communication with LLM systems.
    """

    def __init__(self, cache_path: Optional[str] = None, debug: bool = False):
        """
        Initialize the MCP server.

        Args:
            cache_path: Path to the Granola cache file
            debug: Enable debug logging
        """
        self.cache_path = cache_path
        self.debug = debug
        self.parser: Optional[GranolaParser] = None
        self.tools: Optional[MCPTools] = None
        self.logger = self._setup_logging()

        # MCP server info
        self.server_info = {
            "name": "GranolaMCP",
            "version": "1.0.0",
            "description": "MCP server for Granola.ai meeting data access and analytics"
        }

        # Track initialization state
        self.initialized = False

    def _setup_logging(self) -> logging.Logger:
        """Set up logging for the MCP server."""
        logger = logging.getLogger("granola_mcp")

        if self.debug:
            logger.setLevel(logging.DEBUG)
            handler = logging.StreamHandler(sys.stderr)
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        else:
            logger.setLevel(logging.WARNING)

        return logger

    def _send_response(self, response: Dict[str, Any]) -> None:
        """
        Send a JSON-RPC response to stdout.

        Args:
            response: JSON-RPC response object
        """
        try:
            json_str = json.dumps(response, separators=(',', ':'))
            print(json_str, flush=True)
            self.logger.debug(f"Sent response: {json_str}")
        except Exception as e:
            self.logger.error(f"Error sending response: {e}")

    def _send_error(self, request_id: Optional[Union[str, int]],
                   code: int, message: str, data: Optional[Any] = None) -> None:
        """
        Send a JSON-RPC error response.

        Args:
            request_id: Request ID from the original request
            code: Error code
            message: Error message
            data: Optional error data
        """
        error_response = {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {
                "code": code,
                "message": message
            }
        }

        if data is not None:
            error_response["error"]["data"] = data

        self._send_response(error_response)

    def _handle_initialize(self, request: Dict[str, Any]) -> None:
        """
        Handle MCP initialize request.

        Args:
            request: JSON-RPC initialize request
        """
        try:
            # Initialize parser and tools
            self.parser = GranolaParser(self.cache_path)
            self.tools = MCPTools(self.parser)

            # Validate cache file
            if not self.parser.validate_cache_structure():
                raise GranolaParseError("Invalid cache file structure")

            self.initialized = True

            # Get available tools
            available_tools = self.tools.get_tool_schemas()

            response = {
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": {
                            "listChanged": False
                        }
                    },
                    "serverInfo": self.server_info,
                    "tools": available_tools
                }
            }

            self._send_response(response)
            self.logger.info("MCP server initialized successfully")

        except Exception as e:
            self.logger.error(f"Initialization error: {e}")
            self._send_error(
                request.get("id"),
                -32603,  # Internal error
                f"Failed to initialize server: {str(e)}"
            )

    def _handle_tools_list(self, request: Dict[str, Any]) -> None:
        """
        Handle tools/list request.

        Args:
            request: JSON-RPC tools/list request
        """
        if not self.initialized or not self.tools:
            self._send_error(
                request.get("id"),
                -32002,  # Invalid request
                "Server not initialized"
            )
            return

        try:
            tools = self.tools.get_tool_schemas()

            response = {
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "result": {
                    "tools": tools
                }
            }

            self._send_response(response)

        except Exception as e:
            self.logger.error(f"Error listing tools: {e}")
            self._send_error(
                request.get("id"),
                -32603,  # Internal error
                f"Failed to list tools: {str(e)}"
            )

    def _handle_tools_call(self, request: Dict[str, Any]) -> None:
        """
        Handle tools/call request.

        Args:
            request: JSON-RPC tools/call request
        """
        if not self.initialized or not self.tools:
            self._send_error(
                request.get("id"),
                -32002,  # Invalid request
                "Server not initialized"
            )
            return

        try:
            params = request.get("params", {})
            tool_name = params.get("name")
            tool_arguments = params.get("arguments", {})

            if not tool_name:
                self._send_error(
                    request.get("id"),
                    -32602,  # Invalid params
                    "Missing tool name"
                )
                return

            # Execute the tool
            result = self.tools.execute_tool(tool_name, tool_arguments)

            response = {
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(result, indent=2)
                        }
                    ]
                }
            }

            self._send_response(response)

        except ValueError as e:
            # Tool validation error
            self._send_error(
                request.get("id"),
                -32602,  # Invalid params
                str(e)
            )
        except Exception as e:
            self.logger.error(f"Error executing tool: {e}")
            if self.debug:
                self.logger.error(traceback.format_exc())

            self._send_error(
                request.get("id"),
                -32603,  # Internal error
                f"Tool execution failed: {str(e)}"
            )

    def _handle_ping(self, request: Dict[str, Any]) -> None:
        """
        Handle ping request.

        Args:
            request: JSON-RPC ping request
        """
        response = {
            "jsonrpc": "2.0",
            "id": request.get("id"),
            "result": {}
        }
        self._send_response(response)

    def _handle_request(self, request: Dict[str, Any]) -> None:
        """
        Handle incoming JSON-RPC request.

        Args:
            request: Parsed JSON-RPC request
        """
        method = request.get("method")

        if method == "initialize":
            self._handle_initialize(request)
        elif method == "tools/list":
            self._handle_tools_list(request)
        elif method == "tools/call":
            self._handle_tools_call(request)
        elif method == "ping":
            self._handle_ping(request)
        else:
            self._send_error(
                request.get("id"),
                -32601,  # Method not found
                f"Unknown method: {method}"
            )

    def run(self) -> None:
        """
        Run the MCP server, processing requests from stdin.
        """
        self.logger.info("Starting MCP server...")

        try:
            for line in sys.stdin:
                line = line.strip()
                if not line:
                    continue

                try:
                    request = json.loads(line)
                    self.logger.debug(f"Received request: {request}")
                    self._handle_request(request)

                except json.JSONDecodeError as e:
                    self.logger.error(f"Invalid JSON received: {e}")
                    self._send_error(
                        None,
                        -32700,  # Parse error
                        "Invalid JSON"
                    )
                except Exception as e:
                    self.logger.error(f"Error processing request: {e}")
                    if self.debug:
                        self.logger.error(traceback.format_exc())

                    self._send_error(
                        None,
                        -32603,  # Internal error
                        f"Internal server error: {str(e)}"
                    )

        except KeyboardInterrupt:
            self.logger.info("Server interrupted by user")
        except Exception as e:
            self.logger.error(f"Server error: {e}")
            if self.debug:
                self.logger.error(traceback.format_exc())
        finally:
            self.logger.info("MCP server shutting down")


def main():
    """Main entry point for the MCP server."""
    import argparse

    parser = argparse.ArgumentParser(description="Granola MCP Server")
    parser.add_argument(
        "--cache-path",
        type=str,
        help="Path to Granola cache file"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging"
    )

    args = parser.parse_args()

    server = MCPServer(
        cache_path=args.cache_path,
        debug=args.debug
    )

    server.run()


if __name__ == "__main__":
    main()