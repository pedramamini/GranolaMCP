"""
ANSI color utilities for GranolaMCP CLI.

Provides color constants and utilities for terminal output formatting
using only Python standard library.
"""

import sys
from typing import Optional


class Colors:
    """ANSI color codes and formatting constants."""

    # Reset
    RESET = '\033[0m'

    # Regular colors
    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'

    # Bright colors
    BRIGHT_BLACK = '\033[90m'
    BRIGHT_RED = '\033[91m'
    BRIGHT_GREEN = '\033[92m'
    BRIGHT_YELLOW = '\033[93m'
    BRIGHT_BLUE = '\033[94m'
    BRIGHT_MAGENTA = '\033[95m'
    BRIGHT_CYAN = '\033[96m'
    BRIGHT_WHITE = '\033[97m'

    # Background colors
    BG_BLACK = '\033[40m'
    BG_RED = '\033[41m'
    BG_GREEN = '\033[42m'
    BG_YELLOW = '\033[43m'
    BG_BLUE = '\033[44m'
    BG_MAGENTA = '\033[45m'
    BG_CYAN = '\033[46m'
    BG_WHITE = '\033[47m'

    # Text formatting
    BOLD = '\033[1m'
    DIM = '\033[2m'
    ITALIC = '\033[3m'
    UNDERLINE = '\033[4m'
    BLINK = '\033[5m'
    REVERSE = '\033[7m'
    STRIKETHROUGH = '\033[9m'

    # Semantic colors for CLI
    SUCCESS = GREEN
    ERROR = RED
    WARNING = YELLOW
    INFO = BLUE
    HEADER = BOLD + CYAN
    SUBHEADER = CYAN
    MUTED = DIM
    HIGHLIGHT = BRIGHT_YELLOW

    # Flag to control color output
    _enabled = True

    @classmethod
    def disable(cls) -> None:
        """Disable all color output."""
        cls._enabled = False

    @classmethod
    def enable(cls) -> None:
        """Enable color output."""
        cls._enabled = True

    @classmethod
    def is_enabled(cls) -> bool:
        """Check if colors are enabled."""
        return cls._enabled


def colorize(text: str, color: str, reset: bool = True) -> str:
    """
    Apply color to text.

    Args:
        text: Text to colorize
        color: ANSI color code
        reset: Whether to add reset code at the end

    Returns:
        str: Colorized text (or plain text if colors disabled)
    """
    if not Colors.is_enabled():
        return text

    if reset:
        return f"{color}{text}{Colors.RESET}"
    else:
        return f"{color}{text}"


def bold(text: str) -> str:
    """Make text bold."""
    return colorize(text, Colors.BOLD)


def dim(text: str) -> str:
    """Make text dim."""
    return colorize(text, Colors.DIM)


def underline(text: str) -> str:
    """Make text underlined."""
    return colorize(text, Colors.UNDERLINE)


def success(text: str) -> str:
    """Format text as success message."""
    return colorize(text, Colors.SUCCESS)


def error(text: str) -> str:
    """Format text as error message."""
    return colorize(text, Colors.ERROR)


def warning(text: str) -> str:
    """Format text as warning message."""
    return colorize(text, Colors.WARNING)


def info(text: str) -> str:
    """Format text as info message."""
    return colorize(text, Colors.INFO)


def header(text: str) -> str:
    """Format text as header."""
    return colorize(text, Colors.HEADER)


def subheader(text: str) -> str:
    """Format text as subheader."""
    return colorize(text, Colors.SUBHEADER)


def muted(text: str) -> str:
    """Format text as muted."""
    return colorize(text, Colors.MUTED)


def highlight(text: str) -> str:
    """Format text as highlighted."""
    return colorize(text, Colors.HIGHLIGHT)


def print_colored(text: str, color: str, file=None) -> None:
    """
    Print colored text to specified file.

    Args:
        text: Text to print
        color: ANSI color code
        file: File to print to (default: stdout)
    """
    if file is None:
        file = sys.stdout

    print(colorize(text, color), file=file)


def print_success(text: str, file=None) -> None:
    """Print success message."""
    print_colored(text, Colors.SUCCESS, file)


def print_error(text: str, file=None) -> None:
    """Print error message."""
    print_colored(text, Colors.ERROR, file or sys.stderr)


def print_warning(text: str, file=None) -> None:
    """Print warning message."""
    print_colored(text, Colors.WARNING, file or sys.stderr)


def print_info(text: str, file=None) -> None:
    """Print info message."""
    print_colored(text, Colors.INFO, file)


def print_header(text: str, file=None) -> None:
    """Print header text."""
    print_colored(text, Colors.HEADER, file)


def print_subheader(text: str, file=None) -> None:
    """Print subheader text."""
    print_colored(text, Colors.SUBHEADER, file)


def format_duration(seconds: Optional[float]) -> str:
    """
    Format duration in seconds to human-readable format.

    Args:
        seconds: Duration in seconds

    Returns:
        str: Formatted duration (e.g., "1h 23m", "45m 30s", "2m 15s")
    """
    if seconds is None:
        return muted("Unknown")

    if seconds < 0:
        return muted("Invalid")

    # Convert to integer seconds for display
    total_seconds = int(seconds)

    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    secs = total_seconds % 60

    if hours > 0:
        if minutes > 0:
            return f"{hours}h {minutes}m"
        else:
            return f"{hours}h"
    elif minutes > 0:
        if secs > 0:
            return f"{minutes}m {secs}s"
        else:
            return f"{minutes}m"
    else:
        return f"{secs}s"


def format_participant_count(count: int) -> str:
    """
    Format participant count with appropriate color.

    Args:
        count: Number of participants

    Returns:
        str: Formatted participant count
    """
    if count == 0:
        return muted("0")
    elif count == 1:
        return colorize("1", Colors.YELLOW)
    elif count <= 5:
        return colorize(str(count), Colors.GREEN)
    else:
        return colorize(str(count), Colors.CYAN)


def truncate_text(text: str, max_length: int, suffix: str = "...") -> str:
    """
    Truncate text to maximum length with suffix.

    Args:
        text: Text to truncate
        max_length: Maximum length including suffix
        suffix: Suffix to add when truncating

    Returns:
        str: Truncated text
    """
    if len(text) <= max_length:
        return text

    return text[:max_length - len(suffix)] + suffix


def format_meeting_id(meeting_id: Optional[str], max_length: int = 8) -> str:
    """
    Format meeting ID for display.

    Args:
        meeting_id: Meeting ID to format
        max_length: Maximum length to display

    Returns:
        str: Formatted meeting ID
    """
    if not meeting_id:
        return muted("Unknown")

    # Truncate long IDs for readability
    if len(meeting_id) > max_length:
        truncated = meeting_id[:max_length]
        return colorize(truncated, Colors.BRIGHT_BLUE)
    else:
        return colorize(meeting_id, Colors.BRIGHT_BLUE)