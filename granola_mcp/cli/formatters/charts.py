"""
ASCII chart utilities for GranolaMCP CLI.

Provides functions for creating terminal-friendly charts and visualizations
using Unicode box-drawing characters and ANSI colors.
"""

import math
import shutil
from typing import List, Tuple, Dict, Any, Optional, Union
from .colors import Colors, colorize, muted, header, subheader


class ChartConfig:
    """Configuration for chart appearance."""

    # Unicode box-drawing characters
    HORIZONTAL = '─'
    VERTICAL = '│'
    TOP_LEFT = '┌'
    TOP_RIGHT = '┐'
    BOTTOM_LEFT = '└'
    BOTTOM_RIGHT = '┘'
    CROSS = '┼'
    T_DOWN = '┬'
    T_UP = '┴'
    T_RIGHT = '├'
    T_LEFT = '┤'

    # Bar chart characters
    FULL_BLOCK = '█'
    SEVEN_EIGHTHS = '▉'
    THREE_QUARTERS = '▊'
    FIVE_EIGHTHS = '▋'
    HALF_BLOCK = '▌'
    THREE_EIGHTHS = '▍'
    QUARTER_BLOCK = '▎'
    EIGHTH_BLOCK = '▏'

    # Chart colors
    BAR_COLORS = [
        Colors.BLUE,
        Colors.GREEN,
        Colors.CYAN,
        Colors.MAGENTA,
        Colors.YELLOW,
        Colors.BRIGHT_BLUE,
        Colors.BRIGHT_GREEN,
        Colors.BRIGHT_CYAN,
    ]

    # Default dimensions
    DEFAULT_WIDTH = 60
    DEFAULT_HEIGHT = 15
    MIN_WIDTH = 20
    MIN_HEIGHT = 5


def get_terminal_width() -> int:
    """Get the current terminal width."""
    try:
        return shutil.get_terminal_size().columns
    except:
        return 80


def normalize_data(data: List[Union[int, float]], max_value: Optional[float] = None) -> List[float]:
    """
    Normalize data to 0-1 range for charting.

    Args:
        data: List of numeric values
        max_value: Optional maximum value for normalization

    Returns:
        List[float]: Normalized values
    """
    if not data:
        return []

    if max_value is None:
        max_value = max(data) if data else 1

    if max_value == 0:
        return [0.0] * len(data)

    return [float(value) / max_value for value in data]


def create_bar_chart(
    data: List[Tuple[str, Union[int, float]]],
    title: str = "",
    width: Optional[int] = None,
    height: Optional[int] = None,
    show_values: bool = True,
    color: str = Colors.BLUE
) -> str:
    """
    Create a horizontal bar chart.

    Args:
        data: List of (label, value) tuples
        title: Chart title
        width: Chart width (auto-detected if None)
        height: Chart height (auto-sized if None)
        show_values: Whether to show values next to bars
        color: Color for bars

    Returns:
        str: ASCII bar chart
    """
    if not data:
        return muted("No data to display")

    # Determine dimensions
    terminal_width = get_terminal_width()
    if width is None:
        width = min(ChartConfig.DEFAULT_WIDTH, terminal_width - 10)
    width = max(width, ChartConfig.MIN_WIDTH)

    if height is None:
        height = min(len(data), ChartConfig.DEFAULT_HEIGHT)
    height = max(height, ChartConfig.MIN_HEIGHT)

    # Find the maximum label length and value
    max_label_len = max(len(label) for label, _ in data)
    max_value = max(value for _, value in data) if data else 1

    # Calculate available space for bars
    value_space = 10 if show_values else 0  # Space for value display
    bar_width = width - max_label_len - value_space - 3  # 3 for spacing and border
    bar_width = max(bar_width, 10)  # Minimum bar width

    lines = []

    # Add title
    if title:
        lines.append(header(title))
        lines.append("")

    # Create bars
    for label, value in data:
        # Normalize value to bar width
        if max_value > 0:
            bar_length = int((value / max_value) * bar_width)
            remainder = ((value / max_value) * bar_width) - bar_length
        else:
            bar_length = 0
            remainder = 0

        # Create the bar
        full_blocks = ChartConfig.FULL_BLOCK * bar_length

        # Add partial block for remainder
        partial_block = ""
        if remainder > 0.875:
            partial_block = ChartConfig.SEVEN_EIGHTHS
        elif remainder > 0.75:
            partial_block = ChartConfig.THREE_QUARTERS
        elif remainder > 0.625:
            partial_block = ChartConfig.FIVE_EIGHTHS
        elif remainder > 0.5:
            partial_block = ChartConfig.HALF_BLOCK
        elif remainder > 0.375:
            partial_block = ChartConfig.THREE_EIGHTHS
        elif remainder > 0.25:
            partial_block = ChartConfig.QUARTER_BLOCK
        elif remainder > 0.125:
            partial_block = ChartConfig.EIGHTH_BLOCK

        bar = colorize(full_blocks + partial_block, color)

        # Format the line
        label_padded = label.ljust(max_label_len)
        if show_values:
            if isinstance(value, float):
                value_str = f"{value:.1f}".rjust(8)
            else:
                value_str = str(value).rjust(8)
            line = f"{label_padded} {bar} {muted(value_str)}"
        else:
            line = f"{label_padded} {bar}"

        lines.append(line)

    return "\n".join(lines)


def create_histogram(
    data: List[Union[int, float]],
    bins: int = 10,
    title: str = "",
    width: Optional[int] = None,
    height: Optional[int] = None
) -> str:
    """
    Create a histogram from numeric data.

    Args:
        data: List of numeric values
        bins: Number of histogram bins
        title: Chart title
        width: Chart width
        height: Chart height

    Returns:
        str: ASCII histogram
    """
    if not data:
        return muted("No data to display")

    # Calculate histogram bins
    min_val = min(data)
    max_val = max(data)

    if min_val == max_val:
        # All values are the same
        return create_bar_chart([(f"{min_val}", len(data))], title, width, height)

    bin_width = (max_val - min_val) / bins
    bin_counts = [0] * bins
    bin_labels = []

    # Count values in each bin
    for value in data:
        bin_index = min(int((value - min_val) / bin_width), bins - 1)
        bin_counts[bin_index] += 1

    # Create bin labels
    for i in range(bins):
        bin_start = min_val + i * bin_width
        bin_end = min_val + (i + 1) * bin_width
        if isinstance(min_val, int) and isinstance(max_val, int) and bin_width >= 1:
            label = f"{int(bin_start)}-{int(bin_end)}"
        else:
            label = f"{bin_start:.1f}-{bin_end:.1f}"
        bin_labels.append(label)

    # Create bar chart data
    chart_data: List[Tuple[str, Union[int, float]]] = list(zip(bin_labels, bin_counts))

    return create_bar_chart(chart_data, title, width, height, color=Colors.GREEN)


def create_line_chart(
    data: List[Tuple[str, Union[int, float]]],
    title: str = "",
    width: Optional[int] = None,
    height: Optional[int] = None
) -> str:
    """
    Create a simple line chart using ASCII characters.

    Args:
        data: List of (label, value) tuples
        title: Chart title
        width: Chart width
        height: Chart height

    Returns:
        str: ASCII line chart
    """
    if not data:
        return muted("No data to display")

    # Determine dimensions
    terminal_width = get_terminal_width()
    if width is None:
        width = min(ChartConfig.DEFAULT_WIDTH, terminal_width - 10)
    width = max(width, ChartConfig.MIN_WIDTH)

    if height is None:
        height = ChartConfig.DEFAULT_HEIGHT
    height = max(height, ChartConfig.MIN_HEIGHT)

    # Extract values and normalize
    values = [value for _, value in data]
    labels = [label for label, _ in data]

    if not values:
        return muted("No data to display")

    min_val = min(values)
    max_val = max(values)

    lines = []

    # Add title
    if title:
        lines.append(header(title))
        lines.append("")

    # Create the chart grid
    chart_width = width - 10  # Leave space for y-axis labels
    chart_height = height - 2  # Leave space for x-axis

    # Normalize values to chart height
    if max_val == min_val:
        normalized_values = [chart_height // 2] * len(values)
    else:
        normalized_values = [
            int(((value - min_val) / (max_val - min_val)) * (chart_height - 1))
            for value in values
        ]

    # Create the chart line by line (top to bottom)
    for row in range(chart_height - 1, -1, -1):
        line_chars = []

        # Y-axis label
        if max_val == min_val:
            y_value = max_val
        else:
            y_value = min_val + (row / (chart_height - 1)) * (max_val - min_val)

        if isinstance(y_value, float):
            y_label = f"{y_value:6.1f}"
        else:
            y_label = f"{int(y_value):6d}"

        line_chars.append(muted(y_label))
        line_chars.append(" ")

        # Chart content
        for i, norm_val in enumerate(normalized_values):
            if norm_val == row:
                line_chars.append(colorize("●", Colors.CYAN))
            elif i > 0 and (
                (normalized_values[i-1] < row < norm_val) or
                (norm_val < row < normalized_values[i-1])
            ):
                line_chars.append(colorize("│", Colors.CYAN))
            else:
                line_chars.append(" ")

        lines.append("".join(line_chars))

    # Add x-axis
    x_axis = " " * 8
    for i, label in enumerate(labels):
        if i < chart_width:
            x_axis += label[0] if label else " "
    lines.append(muted(x_axis))

    return "\n".join(lines)


def create_time_pattern_chart(
    hourly_data: Dict[int, int],
    title: str = "Meeting Patterns by Hour"
) -> str:
    """
    Create a chart showing meeting patterns by hour of day.

    Args:
        hourly_data: Dictionary mapping hour (0-23) to count
        title: Chart title

    Returns:
        str: ASCII time pattern chart
    """
    # Create data for all 24 hours
    chart_data = []
    for hour in range(24):
        count = hourly_data.get(hour, 0)
        if hour == 0:
            label = "12AM"
        elif hour < 12:
            label = f"{hour}AM"
        elif hour == 12:
            label = "12PM"
        else:
            label = f"{hour-12}PM"
        chart_data.append((label, count))

    return create_bar_chart(chart_data, title, color=Colors.MAGENTA)


def create_day_pattern_chart(
    daily_data: Dict[int, int],
    title: str = "Meeting Patterns by Day of Week"
) -> str:
    """
    Create a chart showing meeting patterns by day of week.

    Args:
        daily_data: Dictionary mapping weekday (0=Monday) to count
        title: Chart title

    Returns:
        str: ASCII day pattern chart
    """
    days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    chart_data = []

    for i, day in enumerate(days):
        count = daily_data.get(i, 0)
        chart_data.append((day, count))

    return create_bar_chart(chart_data, title, color=Colors.YELLOW)


def create_summary_box(stats: Dict[str, Any], title: str = "Meeting Statistics") -> str:
    """
    Create a summary box with key statistics.

    Args:
        stats: Dictionary of statistics
        title: Box title

    Returns:
        str: ASCII summary box
    """
    lines = []

    # Calculate box width (add 1 extra space to ensure proper right padding)
    max_width = max(len(str(v)) + len(k) + 5 for k, v in stats.items())
    box_width = max(max_width, len(title) + 4, 30)

    # Top border
    lines.append(ChartConfig.TOP_LEFT + ChartConfig.HORIZONTAL * (box_width - 2) + ChartConfig.TOP_RIGHT)

    # Title
    title_padding = (box_width - len(title) - 2) // 2
    title_line = ChartConfig.VERTICAL + " " * title_padding + header(title) + " " * (box_width - len(title) - title_padding - 2) + ChartConfig.VERTICAL
    lines.append(title_line)

    # Separator
    lines.append(ChartConfig.T_RIGHT + ChartConfig.HORIZONTAL * (box_width - 2) + ChartConfig.T_LEFT)

    # Statistics
    for key, value in stats.items():
        if isinstance(value, float):
            value_str = f"{value:.1f}"
        else:
            value_str = str(value)

        colored_value = colorize(value_str, Colors.BRIGHT_CYAN)
        content = f"{key}: {colored_value}"
        # Calculate padding using original value_str length (without color codes)
        padding = box_width - len(key) - len(value_str) - 5
        # Ensure minimum padding of 1 space before right border
        padding = max(padding, 1)
        line = ChartConfig.VERTICAL + f" {content}" + " " * padding + ChartConfig.VERTICAL
        lines.append(line)

    # Bottom border
    lines.append(ChartConfig.BOTTOM_LEFT + ChartConfig.HORIZONTAL * (box_width - 2) + ChartConfig.BOTTOM_RIGHT)

    return "\n".join(lines)