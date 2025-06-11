"""
Main CLI entry point for GranolaMCP.

Provides the command-line interface for exploring Granola.ai meeting data
with subcommands for listing, showing, and exporting meetings.
"""

import argparse
import sys
import os
from typing import Optional, List
from ..utils.config import get_cache_path, validate_cache_path
from ..core.parser import GranolaParser, GranolaParseError
from .commands.list import ListCommand
from .commands.show import ShowCommand
from .commands.export import ExportCommand
from .commands.stats import StatsCommand
from .formatters.colors import Colors, colorize


def create_parser() -> argparse.ArgumentParser:
    """
    Create the main argument parser with all subcommands.

    Returns:
        argparse.ArgumentParser: Configured argument parser
    """
    parser = argparse.ArgumentParser(
        prog='granola',
        description='Explore Granola.ai meeting data from the command line',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # List recent meetings
  granola list --last 7d

  # List meetings in date range
  granola list --from 2025-01-01 --to 2025-01-31

  # Search meetings by title
  granola list --title-contains "standup"

  # Show meeting details
  granola show <meeting-id>

  # Show meeting with transcript
  granola show <meeting-id> --transcript

  # Export meeting to markdown
  granola export <meeting-id>
  granola export <meeting-id> > meeting.md

  # Generate statistics
  granola stats --summary
  granola stats --meetings-per-day --last 30d
  granola stats --duration-distribution
  granola stats --participant-frequency

For more help on a specific command, use:
  granola <command> --help
        """
    )

    # Global options
    parser.add_argument(
        '--cache-path',
        type=str,
        help='Path to Granola cache file (overrides config)'
    )

    parser.add_argument(
        '--timezone',
        type=str,
        default='CST',
        help='Timezone for date display (default: CST)'
    )

    parser.add_argument(
        '--no-color',
        action='store_true',
        help='Disable colored output'
    )

    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose output'
    )

    # Create subparsers
    subparsers = parser.add_subparsers(
        dest='command',
        help='Available commands',
        metavar='COMMAND'
    )

    # List command
    list_parser = subparsers.add_parser(
        'list',
        help='List meetings with optional filters',
        description='List meetings from the Granola cache with various filtering options'
    )
    ListCommand.add_arguments(list_parser)

    # Show command
    show_parser = subparsers.add_parser(
        'show',
        help='Show detailed meeting information',
        description='Display detailed information about a specific meeting'
    )
    ShowCommand.add_arguments(show_parser)

    # Export command
    export_parser = subparsers.add_parser(
        'export',
        help='Export meeting to markdown',
        description='Export meeting data to markdown format'
    )
    ExportCommand.add_arguments(export_parser)

    # Stats command
    stats_parser = subparsers.add_parser(
        'stats',
        help='Generate meeting statistics and visualizations',
        description='Analyze meeting data and generate comprehensive statistics with ASCII charts'
    )
    StatsCommand.add_arguments(stats_parser)

    return parser


def validate_cache_file(cache_path: str) -> bool:
    """
    Validate that the cache file exists and is readable.

    Args:
        cache_path: Path to cache file

    Returns:
        bool: True if valid, False otherwise
    """
    if not os.path.exists(cache_path):
        print(colorize(f"Error: Cache file not found: {cache_path}", Colors.RED), file=sys.stderr)
        print(f"Please check your cache path configuration.", file=sys.stderr)
        return False

    if not validate_cache_path(cache_path):
        print(colorize(f"Error: Cache file is not readable: {cache_path}", Colors.RED), file=sys.stderr)
        return False

    return True


def setup_colors(no_color: bool) -> None:
    """
    Setup color configuration based on user preference and terminal support.

    Args:
        no_color: Whether to disable colors
    """
    if no_color or not sys.stdout.isatty():
        Colors.disable()


def main(argv: Optional[List[str]] = None) -> int:
    """
    Main CLI entry point.

    Args:
        argv: Command line arguments (for testing)

    Returns:
        int: Exit code (0 for success, non-zero for error)
    """
    parser = create_parser()
    args = parser.parse_args(argv)

    # Setup colors
    setup_colors(args.no_color)

    # Show help if no command specified
    if not args.command:
        parser.print_help()
        return 1

    # Determine cache path
    cache_path = args.cache_path or get_cache_path()

    if args.verbose:
        print(f"Using cache file: {cache_path}")

    # Validate cache file
    if not validate_cache_file(cache_path):
        return 1

    # Create parser
    try:
        granola_parser = GranolaParser(cache_path)

        # Test that we can load the cache
        granola_parser.load_cache()

        if args.verbose:
            cache_info = granola_parser.get_cache_info()
            print(f"Cache loaded successfully: {cache_info['meeting_count']} meetings found")

    except GranolaParseError as e:
        print(colorize(f"Error parsing cache file: {e}", Colors.RED), file=sys.stderr)
        return 1
    except Exception as e:
        print(colorize(f"Unexpected error: {e}", Colors.RED), file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1

    # Execute command
    try:
        if args.command == 'list':
            command = ListCommand(granola_parser, args)
            return command.execute()
        elif args.command == 'show':
            command = ShowCommand(granola_parser, args)
            return command.execute()
        elif args.command == 'export':
            command = ExportCommand(granola_parser, args)
            return command.execute()
        elif args.command == 'stats':
            command = StatsCommand(granola_parser, args)
            return command.execute()
        else:
            print(colorize(f"Unknown command: {args.command}", Colors.RED), file=sys.stderr)
            return 1

    except KeyboardInterrupt:
        print(colorize("\nOperation cancelled by user", Colors.YELLOW), file=sys.stderr)
        return 130
    except Exception as e:
        print(colorize(f"Error executing command: {e}", Colors.RED), file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())