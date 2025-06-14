"""
List command implementation for GranolaMCP CLI.

Provides functionality to list meetings with various filtering options
including date ranges, title search, and participant filtering.
"""

import argparse
import datetime
from typing import List, Optional, Dict, Any
from ...core.parser import GranolaParser
from ...core.meeting import Meeting
from ...utils.date_parser import parse_date, get_date_range
from ..formatters.colors import (
    Colors, colorize, format_duration,
    format_meeting_id, print_error, print_info, muted
)
from ..formatters.table import Table, TableAlignment


class ListCommand:
    """Command to list meetings with filtering options."""

    def __init__(self, parser: GranolaParser, args: argparse.Namespace):
        """
        Initialize the list command.

        Args:
            parser: GranolaParser instance
            args: Parsed command line arguments
        """
        self.parser = parser
        self.args = args

    @staticmethod
    def add_arguments(parser: argparse.ArgumentParser) -> None:
        """
        Add arguments for the list command.

        Args:
            parser: Argument parser to add arguments to
        """
        # Date filtering options
        date_group = parser.add_mutually_exclusive_group()
        date_group.add_argument(
            '--last',
            type=str,
            help='Show meetings from the last period (e.g., 3d, 24h, 1w, 2m)'
        )

        date_group.add_argument(
            '--from',
            dest='from_date',
            type=str,
            help='Start date for filtering (YYYY-MM-DD or relative like 7d)'
        )

        parser.add_argument(
            '--to',
            dest='to_date',
            type=str,
            help='End date for filtering (YYYY-MM-DD or relative like 1d). Only used with --from'
        )

        # Content filtering options
        parser.add_argument(
            '--title-contains',
            type=str,
            help='Filter meetings by title content (case-insensitive)'
        )

        parser.add_argument(
            '--participant',
            type=str,
            help='Filter meetings by participant email/name'
        )

        parser.add_argument(
            '--folder',
            type=str,
            help='Filter meetings by folder/list name (case-insensitive)'
        )

        # Sorting options
        parser.add_argument(
            '--sort-by',
            choices=['date', 'title', 'duration', 'participants'],
            default='date',
            help='Sort meetings by field (default: date)'
        )

        parser.add_argument(
            '--reverse',
            action='store_true',
            help='Reverse sort order'
        )

        # Output options
        parser.add_argument(
            '--limit',
            type=int,
            help='Limit number of results'
        )

        parser.add_argument(
            '--format',
            choices=['table', 'simple', 'ids'],
            default='table',
            help='Output format (default: table)'
        )

        parser.add_argument(
            '--no-header',
            action='store_true',
            help='Hide table header'
        )

    def _filter_meetings_by_date(self, meetings: List[Meeting]) -> List[Meeting]:
        """
        Filter meetings by date criteria.

        Args:
            meetings: List of meetings to filter

        Returns:
            List[Meeting]: Filtered meetings
        """
        if not self.args.last and not self.args.from_date:
            return meetings

        try:
            if self.args.last:
                # Filter by relative date
                start_date = parse_date(self.args.last)
                end_date = datetime.datetime.now(start_date.tzinfo)  # Use same timezone
            else:
                # Filter by date range
                start_date, end_date = get_date_range(
                    self.args.from_date,
                    self.args.to_date
                )

            filtered_meetings = []
            for meeting in meetings:
                if meeting.start_time and start_date <= meeting.start_time <= end_date:
                    filtered_meetings.append(meeting)

            return filtered_meetings

        except ValueError as e:
            print_error(f"Invalid date format: {e}")
            return []

    def _filter_meetings_by_title(self, meetings: List[Meeting]) -> List[Meeting]:
        """
        Filter meetings by title content.

        Args:
            meetings: List of meetings to filter

        Returns:
            List[Meeting]: Filtered meetings
        """
        if not self.args.title_contains:
            return meetings

        search_term = self.args.title_contains.lower()
        filtered_meetings = []

        for meeting in meetings:
            title = meeting.title or ""
            if search_term in title.lower():
                filtered_meetings.append(meeting)

        return filtered_meetings

    def _filter_meetings_by_participant(self, meetings: List[Meeting]) -> List[Meeting]:
        """
        Filter meetings by participant.

        Args:
            meetings: List of meetings to filter

        Returns:
            List[Meeting]: Filtered meetings
        """
        if not self.args.participant:
            return meetings

        search_term = self.args.participant.lower()
        filtered_meetings = []

        for meeting in meetings:
            participants = meeting.participants
            for participant in participants:
                if search_term in participant.lower():
                    filtered_meetings.append(meeting)
                    break

        return filtered_meetings

    def _filter_meetings_by_folder(self, meetings: List[Meeting]) -> List[Meeting]:
        """
        Filter meetings by folder/list name.

        Args:
            meetings: List of meetings to filter

        Returns:
            List[Meeting]: Filtered meetings
        """
        if not self.args.folder:
            return meetings

        search_term = self.args.folder.lower()
        filtered_meetings = []

        for meeting in meetings:
            folder_name = meeting.folder_name or ""
            if search_term in folder_name.lower():
                filtered_meetings.append(meeting)

        return filtered_meetings

    def _sort_meetings(self, meetings: List[Meeting]) -> List[Meeting]:
        """
        Sort meetings by specified criteria.

        Args:
            meetings: List of meetings to sort

        Returns:
            List[Meeting]: Sorted meetings
        """
        def sort_key(meeting: Meeting):
            if self.args.sort_by == 'title':
                return meeting.title or ""
            elif self.args.sort_by == 'duration':
                duration = meeting.duration
                return duration.total_seconds() if duration else 0
            elif self.args.sort_by == 'participants':
                return len(meeting.participants)
            else:  # date
                return meeting.start_time or datetime.datetime.min

        return sorted(meetings, key=sort_key, reverse=self.args.reverse)

    def _calculate_stats(self, meetings: List[Meeting]) -> Dict[str, Any]:
        """
        Calculate statistics for the meetings.

        Args:
            meetings: List of meetings to calculate stats for

        Returns:
            Dict[str, Any]: Statistics dictionary
        """
        stats = {
            'total_meetings': len(meetings),
            'total_duration_seconds': 0,
            'meetings_with_duration': 0,
            'unique_dates': set()
        }

        for meeting in meetings:
            if meeting.duration:
                stats['total_duration_seconds'] += meeting.duration.total_seconds()
                stats['meetings_with_duration'] += 1
            
            if meeting.start_time:
                # Track unique dates (just the date part, not time)
                date_only = meeting.start_time.date()
                stats['unique_dates'].add(date_only)

        stats['unique_days'] = len(stats['unique_dates'])
        stats['avg_hours_per_day'] = 0

        if stats['unique_days'] > 0 and stats['total_duration_seconds'] > 0:
            total_hours = stats['total_duration_seconds'] / 3600
            stats['avg_hours_per_day'] = total_hours / stats['unique_days']

        return stats

    def _format_table_output(self, meetings: List[Meeting]) -> None:
        """
        Format meetings as a table.

        Args:
            meetings: List of meetings to display
        """
        if not meetings:
            print_info("No meetings found matching the criteria.")
            return

        # Create table
        headers = ['ID', 'Title', 'Date', 'Duration', 'Transcript', 'Summary', 'Folder']
        alignments = [
            TableAlignment.LEFT,
            TableAlignment.LEFT,
            TableAlignment.LEFT,
            TableAlignment.RIGHT,
            TableAlignment.RIGHT,
            TableAlignment.RIGHT,
            TableAlignment.LEFT
        ]

        table = Table(headers, alignments)
        table.show_header = not self.args.no_header

        for meeting in meetings:
            # Format each field
            meeting_id = format_meeting_id(meeting.id)

            title = meeting.title or muted("Untitled")
            if len(title) > 40:
                title = title[:37] + "..."

            date_str = muted("Unknown")
            if meeting.start_time:
                date_str = meeting.start_time.strftime("%m/%d %H:%M")

            # Try to get actual meeting duration
            duration_str = muted("Unknown")
            
            # First try the meeting's duration property (uses start/end times)
            if meeting.duration:
                duration_str = format_duration(meeting.duration.total_seconds())
            else:
                # Try to get duration from transcript timing
                if meeting.has_transcript():
                    try:
                        transcript = meeting.transcript
                        segments = transcript.segments
                        if segments and len(segments) > 0:
                            first = segments[0]
                            last = segments[-1]
                            if hasattr(last, 'end_time') and hasattr(first, 'start_time') and last.end_time and first.start_time:
                                duration_seconds = last.end_time - first.start_time
                                if duration_seconds > 60:  # Only show if > 1 minute
                                    duration_str = format_duration(duration_seconds)
                    except:
                        pass

            # Get transcript word count
            transcript_str = muted("--")
            if meeting.has_transcript():
                transcript = meeting.transcript
                word_count = transcript.word_count
                if word_count > 0:
                    if word_count >= 1000:
                        transcript_str = f"{word_count // 1000:.1f}k"
                    else:
                        transcript_str = str(word_count)

            # Get summary word count  
            summary_str = muted("--")
            summary = meeting.summary
            if summary:
                word_count = len(summary.split())
                if word_count > 0:
                    summary_str = str(word_count)

            # Get folder name
            folder_str = meeting.folder_name or muted("--")
            if folder_str and len(folder_str) > 15:
                folder_str = folder_str[:12] + "..."

            table.add_row([meeting_id, title, date_str, duration_str, transcript_str, summary_str, folder_str])

        table.print()

        # Add statistics at the bottom
        stats = self._calculate_stats(meetings)
        if stats['total_meetings'] > 0:
            print()  # Empty line before stats
            total_duration_str = format_duration(stats['total_duration_seconds'])
            
            # Format average hours per day
            avg_hours = stats['avg_hours_per_day']
            if avg_hours >= 1:
                avg_str = f"{avg_hours:.1f}h"
            elif avg_hours > 0:
                avg_minutes = avg_hours * 60
                avg_str = f"{avg_minutes:.0f}m"
            else:
                avg_str = "0m"

            print(f"📊 Total meeting time: {colorize(total_duration_str, Colors.CYAN)}")
            print(f"📈 Average per day ({stats['unique_days']} days): {colorize(avg_str, Colors.GREEN)}")

    def _format_simple_output(self, meetings: List[Meeting]) -> None:
        """
        Format meetings as simple text output.

        Args:
            meetings: List of meetings to display
        """
        if not meetings:
            print_info("No meetings found matching the criteria.")
            return

        for i, meeting in enumerate(meetings):
            if i > 0:
                print()

            # Meeting header
            title = meeting.title or "Untitled Meeting"
            print(colorize(title, Colors.HEADER))

            # Meeting details
            details = []

            if meeting.id:
                details.append(f"ID: {format_meeting_id(meeting.id, max_length=12)}")

            if meeting.start_time:
                details.append(f"Date: {meeting.start_time.strftime('%Y-%m-%d %H:%M')}")

            if meeting.duration:
                duration_str = format_duration(meeting.duration.total_seconds())
                details.append(f"Duration: {duration_str}")

            if meeting.participants:
                details.append(f"Participants: {len(meeting.participants)}")

            if details:
                print(muted(" | ".join(details)))

    def _format_ids_output(self, meetings: List[Meeting]) -> None:
        """
        Format meetings as ID-only output.

        Args:
            meetings: List of meetings to display
        """
        for meeting in meetings:
            if meeting.id:
                print(meeting.id)

    def execute(self) -> int:
        """
        Execute the list command.

        Returns:
            int: Exit code (0 for success)
        """
        try:
            # Load meetings with debug flag if verbose is enabled
            debug_flag = getattr(self.args, 'verbose', False)
            meeting_data = self.parser.get_meetings(debug=debug_flag)
            meetings = [Meeting(data) for data in meeting_data]

            if self.args.verbose:
                print_info(f"Loaded {len(meetings)} meetings from cache")

            # Apply filters
            meetings = self._filter_meetings_by_date(meetings)
            meetings = self._filter_meetings_by_title(meetings)
            meetings = self._filter_meetings_by_participant(meetings)
            meetings = self._filter_meetings_by_folder(meetings)

            # Sort meetings
            meetings = self._sort_meetings(meetings)

            # Apply limit
            if self.args.limit and self.args.limit > 0:
                meetings = meetings[:self.args.limit]

            # Format output
            if self.args.format == 'simple':
                self._format_simple_output(meetings)
            elif self.args.format == 'ids':
                self._format_ids_output(meetings)
            else:  # table
                self._format_table_output(meetings)

            return 0

        except Exception as e:
            print_error(f"Error listing meetings: {e}")
            if self.args.verbose:
                import traceback
                traceback.print_exc()
            return 1