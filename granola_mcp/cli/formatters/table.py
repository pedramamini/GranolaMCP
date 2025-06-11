"""
ASCII table formatting utilities for GranolaMCP CLI.

Provides functions for creating formatted tables with borders, alignment,
and color support using only Python standard library.
"""

from typing import List, Dict, Any, Optional, Union
from .colors import Colors, colorize


class TableAlignment:
    """Table column alignment constants."""
    LEFT = 'left'
    RIGHT = 'right'
    CENTER = 'center'


class Table:
    """
    ASCII table formatter with support for colors and alignment.
    """

    def __init__(self, headers: List[str], alignments: Optional[List[str]] = None):
        """
        Initialize table with headers and optional alignments.

        Args:
            headers: List of column headers
            alignments: List of alignment strings (left, right, center)
        """
        self.headers = headers
        self.rows: List[List[str]] = []
        self.alignments = alignments or [TableAlignment.LEFT] * len(headers)
        self.column_widths: List[int] = [len(header) for header in headers]

        # Table styling
        self.border_color = Colors.BRIGHT_BLACK
        self.header_color = Colors.HEADER
        self.show_borders = True
        self.show_header = True

    def add_row(self, row: List[str]) -> None:
        """
        Add a row to the table.

        Args:
            row: List of cell values
        """
        if len(row) != len(self.headers):
            raise ValueError(f"Row must have {len(self.headers)} columns, got {len(row)}")

        # Convert all values to strings and update column widths
        str_row = []
        for i, cell in enumerate(row):
            cell_str = str(cell) if cell is not None else ""
            str_row.append(cell_str)

            # Update column width (accounting for ANSI codes)
            display_width = self._get_display_width(cell_str)
            self.column_widths[i] = max(self.column_widths[i], display_width)

        self.rows.append(str_row)

    def _get_display_width(self, text: str) -> int:
        """
        Get the display width of text, ignoring ANSI escape codes.

        Args:
            text: Text that may contain ANSI codes

        Returns:
            int: Display width
        """
        import re
        # Remove ANSI escape codes for width calculation
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        clean_text = ansi_escape.sub('', text)
        return len(clean_text)

    def _pad_cell(self, text: str, width: int, alignment: str) -> str:
        """
        Pad cell text according to alignment and width.

        Args:
            text: Cell text
            width: Target width
            alignment: Alignment type

        Returns:
            str: Padded text
        """
        display_width = self._get_display_width(text)
        padding_needed = width - display_width

        if padding_needed <= 0:
            return text

        if alignment == TableAlignment.RIGHT:
            return ' ' * padding_needed + text
        elif alignment == TableAlignment.CENTER:
            left_padding = padding_needed // 2
            right_padding = padding_needed - left_padding
            return ' ' * left_padding + text + ' ' * right_padding
        else:  # LEFT
            return text + ' ' * padding_needed

    def _create_border_line(self, line_type: str = 'middle') -> str:
        """
        Create a border line for the table.

        Args:
            line_type: Type of line ('top', 'middle', 'bottom')

        Returns:
            str: Border line
        """
        if not self.show_borders:
            return ""

        if line_type == 'top':
            left, middle, right, cross = '┌', '─', '┐', '┬'
        elif line_type == 'bottom':
            left, middle, right, cross = '└', '─', '┘', '┴'
        else:  # middle
            left, middle, right, cross = '├', '─', '┤', '┼'

        parts = [left]
        for i, width in enumerate(self.column_widths):
            parts.append(middle * (width + 2))  # +2 for padding
            if i < len(self.column_widths) - 1:
                parts.append(cross)
        parts.append(right)

        return colorize(''.join(parts), self.border_color)

    def _create_row_line(self, row: List[str], is_header: bool = False) -> str:
        """
        Create a formatted row line.

        Args:
            row: Row data
            is_header: Whether this is a header row

        Returns:
            str: Formatted row line
        """
        parts = []

        if self.show_borders:
            parts.append(colorize('│', self.border_color))

        for i, (cell, width, alignment) in enumerate(zip(row, self.column_widths, self.alignments)):
            padded_cell = self._pad_cell(cell, width, alignment)

            if is_header:
                padded_cell = colorize(padded_cell, self.header_color)

            parts.append(f' {padded_cell} ')

            if self.show_borders and i < len(row) - 1:
                parts.append(colorize('│', self.border_color))

        if self.show_borders:
            parts.append(colorize('│', self.border_color))

        return ''.join(parts)

    def render(self) -> str:
        """
        Render the complete table as a string.

        Returns:
            str: Formatted table
        """
        lines = []

        # Top border
        if self.show_borders:
            lines.append(self._create_border_line('top'))

        # Header
        if self.show_header:
            lines.append(self._create_row_line(self.headers, is_header=True))

            if self.show_borders and self.rows:
                lines.append(self._create_border_line('middle'))

        # Data rows
        for i, row in enumerate(self.rows):
            lines.append(self._create_row_line(row))

            # Add separator between rows if needed (not implemented for now)

        # Bottom border
        if self.show_borders:
            lines.append(self._create_border_line('bottom'))

        return '\n'.join(lines)

    def print(self) -> None:
        """Print the table to stdout."""
        print(self.render())


def create_simple_table(data: List[Dict[str, Any]], headers: Optional[List[str]] = None,
                       alignments: Optional[List[str]] = None) -> Table:
    """
    Create a simple table from a list of dictionaries.

    Args:
        data: List of dictionaries with consistent keys
        headers: Optional custom headers (uses dict keys if not provided)
        alignments: Optional column alignments

    Returns:
        Table: Configured table object
    """
    if not data:
        return Table(headers or [], alignments)

    # Use first row keys as headers if not provided
    if headers is None:
        headers = list(data[0].keys())

    table = Table(headers, alignments)

    for row_dict in data:
        row = [str(row_dict.get(header, "")) for header in headers]
        table.add_row(row)

    return table


def print_key_value_pairs(pairs: List[tuple], indent: int = 0,
                         key_color: str = Colors.CYAN, value_color: str = Colors.WHITE) -> None:
    """
    Print key-value pairs in a formatted way.

    Args:
        pairs: List of (key, value) tuples
        indent: Number of spaces to indent
        key_color: Color for keys
        value_color: Color for values
    """
    if not pairs:
        return

    # Find the maximum key length for alignment
    max_key_length = max(len(str(key)) for key, _ in pairs)

    indent_str = ' ' * indent

    for key, value in pairs:
        key_str = colorize(f"{key}:".ljust(max_key_length + 1), key_color)
        value_str = colorize(str(value), value_color)
        print(f"{indent_str}{key_str} {value_str}")


def print_section(title: str, content: Optional[str] = None,
                 title_color: str = Colors.HEADER, border_char: str = '─') -> None:
    """
    Print a section with title and optional content.

    Args:
        title: Section title
        content: Optional section content
        title_color: Color for the title
        border_char: Character for the border line
    """
    print()
    print(colorize(title, title_color))
    print(colorize(border_char * len(title), title_color))

    if content:
        print(content)


def print_list_items(items: List[str], bullet: str = '•',
                    bullet_color: str = Colors.CYAN, indent: int = 2) -> None:
    """
    Print a list of items with bullets.

    Args:
        items: List of items to print
        bullet: Bullet character
        bullet_color: Color for bullets
        indent: Number of spaces to indent
    """
    indent_str = ' ' * indent
    colored_bullet = colorize(bullet, bullet_color)

    for item in items:
        print(f"{indent_str}{colored_bullet} {item}")