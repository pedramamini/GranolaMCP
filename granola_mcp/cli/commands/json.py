"""
JSON command implementation for GranolaMCP CLI.

Provides functionality to extract and pretty-print the JSON data
embedded in the Granola cache file.
"""

import argparse
import json
import sys
from typing import Optional
from ...core.parser import GranolaParser
from ..formatters.colors import print_error


class JsonCommand:
    """Command to extract and pretty-print JSON data from cache."""

    def __init__(self, parser: GranolaParser, args: argparse.Namespace):
        """
        Initialize the JSON command.

        Args:
            parser: GranolaParser instance
            args: Parsed command line arguments
        """
        self.parser = parser
        self.args = args

    @staticmethod
    def add_arguments(parser: argparse.ArgumentParser) -> None:
        """
        Add arguments for the JSON command.

        Args:
            parser: Argument parser to add arguments to
        """
        parser.add_argument(
            '--indent',
            type=int,
            default=2,
            help='JSON indentation level (default: 2)'
        )

        parser.add_argument(
            '--compact',
            action='store_true',
            help='Output compact JSON (no indentation)'
        )

        parser.add_argument(
            '--sort-keys',
            action='store_true',
            help='Sort JSON keys alphabetically'
        )

    def execute(self) -> int:
        """
        Execute the JSON command.

        Returns:
            int: Exit code (0 for success)
        """
        try:
            # Load the inner cache data (already parsed from the embedded JSON string)
            cache_data = self.parser.load_cache()

            # Determine JSON formatting options
            if self.args.compact:
                indent = None
                separators = (',', ':')
            else:
                indent = self.args.indent
                separators = (',', ': ')

            # Pretty print the JSON data
            json_output = json.dumps(
                cache_data,
                indent=indent,
                separators=separators,
                sort_keys=self.args.sort_keys,
                ensure_ascii=False
            )

            # Output to stdout (can be piped)
            print(json_output)

            return 0

        except Exception as e:
            print_error(f"Error extracting JSON data: {e}")
            if self.args.verbose:
                import traceback
                traceback.print_exc()
            return 1