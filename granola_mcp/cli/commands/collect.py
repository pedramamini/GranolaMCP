"""
Collect command implementation for GranolaMCP CLI.

Provides functionality to collect and export your own words (microphone audio)
from meetings within a date range, organized by day into separate text files.
"""

import argparse
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from ...core.parser import GranolaParser
from ...core.meeting import Meeting
from ...core.transcript import Transcript, TranscriptSegment
from ..formatters.colors import print_error, print_info, print_success
from ...utils.date_parser import get_date_range, parse_date


class CollectCommand:
    """Command to collect your own words from meetings over a date range."""

    def __init__(self, parser: GranolaParser, args: argparse.Namespace):
        """
        Initialize the collect command.

        Args:
            parser: GranolaParser instance
            args: Parsed command line arguments
        """
        self.parser = parser
        self.args = args

    @staticmethod
    def add_arguments(parser: argparse.ArgumentParser) -> None:
        """
        Add arguments for the collect command.

        Args:
            parser: Argument parser to add arguments to
        """
        # Date range options
        parser.add_argument(
            '--last',
            type=str,
            help='Collect from last X time (e.g., "7d", "2w", "1m")'
        )

        parser.add_argument(
            '--from',
            dest='from_date',
            type=str,
            help='Start date (YYYY-MM-DD or relative like "7d")'
        )

        parser.add_argument(
            '--to',
            dest='to_date',
            type=str,
            help='End date (YYYY-MM-DD or relative like "1d")'
        )

        # Output options
        parser.add_argument(
            '--output-dir', '-o',
            type=str,
            required=True,
            help='Output directory for collected text files'
        )

        parser.add_argument(
            '--include-timestamps',
            action='store_true',
            help='Include timestamps in the output'
        )

        parser.add_argument(
            '--include-meeting-info',
            action='store_true',
            help='Include meeting title and metadata at the start of each day'
        )

        parser.add_argument(
            '--min-words',
            type=int,
            default=1,
            help='Minimum words required to include a segment (default: 1)'
        )

    def _get_date_range(self) -> Tuple[Optional[datetime], Optional[datetime]]:
        """
        Get the date range for collection.

        Returns:
            Tuple of (start_date, end_date) or (None, None) if invalid
        """
        try:
            if self.args.last:
                return get_date_range(self.args.last)
            elif self.args.from_date or self.args.to_date:
                if self.args.from_date and self.args.to_date:
                    return get_date_range(self.args.from_date, self.args.to_date)
                elif self.args.from_date:
                    from_date = parse_date(self.args.from_date)
                    return from_date, datetime.now(from_date.tzinfo)
                elif self.args.to_date:
                    to_date = parse_date(self.args.to_date)
                    # Default to 7 days before to_date
                    from_date = to_date - timedelta(days=7)
                    return from_date, to_date
            else:
                # Default to last 7 days
                return get_date_range("7d")
        except Exception as e:
            print_error(f"Invalid date range: {e}")
            return None, None

    def _filter_my_words(self, transcript: Transcript) -> List[TranscriptSegment]:
        """
        Filter transcript segments to only include microphone source (my words).

        Args:
            transcript: Transcript to filter

        Returns:
            List of segments that are from microphone source
        """
        my_segments = []
        
        for segment in transcript.segments:
            # Check if this segment is from microphone (my words)
            if hasattr(segment, '_data') and segment._data.get('source') == 'microphone':
                # Filter by minimum words if specified
                if len(segment.text.split()) >= self.args.min_words:
                    my_segments.append(segment)
        
        return my_segments

    def _group_segments_by_date(self, meetings: List[Meeting]) -> Dict[str, List[Tuple[Meeting, List[TranscriptSegment]]]]:
        """
        Group transcript segments by date.

        Args:
            meetings: List of meetings to process

        Returns:
            Dictionary mapping date strings (YYYY-MM-DD) to list of (meeting, segments) tuples
        """
        date_groups = {}
        
        for meeting in meetings:
            transcript = meeting.transcript
            if not transcript:
                continue
                
            # Get my words from this meeting
            my_segments = self._filter_my_words(transcript)
            if not my_segments:
                continue
                
            # Group by date based on meeting start time
            meeting_start_time = meeting.start_time
            if meeting_start_time:
                date_str = meeting_start_time.strftime('%Y-%m-%d')
                if date_str not in date_groups:
                    date_groups[date_str] = []
                date_groups[date_str].append((meeting, my_segments))
        
        return date_groups

    def _format_segments_for_file(self, meeting: Meeting, segments: List[TranscriptSegment]) -> str:
        """
        Format segments for writing to a file.

        Args:
            meeting: Meeting the segments belong to
            segments: List of segments to format

        Returns:
            Formatted string for file output
        """
        lines = []
        
        # Add meeting info if requested
        if self.args.include_meeting_info:
            lines.append(f"# Meeting: {meeting.title or 'Untitled Meeting'}")
            if meeting.start_time:
                lines.append(f"# Date: {meeting.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
            lines.append("")
        
        # Add segments
        for segment in segments:
            if self.args.include_timestamps and segment.timestamp:
                timestamp_str = segment.timestamp.strftime('%H:%M:%S')
                lines.append(f"[{timestamp_str}] {segment.text}")
            else:
                lines.append(segment.text)
        
        return '\n'.join(lines)

    def _write_daily_file(self, date_str: str, content: str) -> None:
        """
        Write content to a daily file.

        Args:
            date_str: Date string (YYYY-MM-DD)
            content: Content to write
        """
        filename = f"{date_str}.txt"
        filepath = os.path.join(self.args.output_dir, filename)
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            
            word_count = len(content.split())
            if self.args.verbose:
                print_info(f"Created {filename} ({word_count} words)")
        
        except Exception as e:
            print_error(f"Error writing {filename}: {e}")
            raise

    def execute(self) -> int:
        """
        Execute the collect command.

        Returns:
            int: Exit code (0 for success)
        """
        try:
            # Get date range
            start_date, end_date = self._get_date_range()
            if start_date is None or end_date is None:
                return 1

            if self.args.verbose:
                print_info(f"Collecting from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")

            # Create output directory
            os.makedirs(self.args.output_dir, exist_ok=True)

            # Get meetings in date range
            meetings = []
            for meeting_data in self.parser.get_meetings():
                meeting = Meeting(meeting_data)
                if meeting.start_time and start_date <= meeting.start_time <= end_date:
                    meetings.append(meeting)

            if not meetings:
                print_info("No meetings found in the specified date range")
                return 0

            if self.args.verbose:
                print_info(f"Found {len(meetings)} meetings")

            # Group segments by date
            date_groups = self._group_segments_by_date(meetings)

            if not date_groups:
                print_info("No words found from microphone source in the specified date range")
                return 0

            # Write daily files
            total_words = 0
            for date_str in sorted(date_groups.keys()):
                meeting_segments = date_groups[date_str]
                
                # Combine all segments for this date
                all_content = []
                for meeting, segments in meeting_segments:
                    content = self._format_segments_for_file(meeting, segments)
                    if content.strip():
                        all_content.append(content)
                        all_content.append("")  # Add blank line between meetings
                
                if all_content:
                    daily_content = '\n'.join(all_content).strip()
                    self._write_daily_file(date_str, daily_content)
                    total_words += len(daily_content.split())

            print_success(f"Collected {total_words} words across {len(date_groups)} days")
            print_info(f"Files saved to: {self.args.output_dir}")

            return 0

        except Exception as e:
            print_error(f"Error collecting words: {e}")
            if self.args.verbose:
                import traceback
                traceback.print_exc()
            return 1