"""
Export command implementation for GranolaMCP CLI.

Provides functionality to export meeting data to markdown format
suitable for documentation and sharing.
"""

import argparse
import sys
from typing import Optional
from ...core.parser import GranolaParser
from ...core.meeting import Meeting
from ..formatters.colors import print_error, print_info
from ..formatters.markdown import export_meeting_to_markdown


class ExportCommand:
    """Command to export meeting data to markdown."""

    def __init__(self, parser: GranolaParser, args: argparse.Namespace):
        """
        Initialize the export command.

        Args:
            parser: GranolaParser instance
            args: Parsed command line arguments
        """
        self.parser = parser
        self.args = args

    @staticmethod
    def add_arguments(parser: argparse.ArgumentParser) -> None:
        """
        Add arguments for the export command.

        Args:
            parser: Argument parser to add arguments to
        """
        parser.add_argument(
            'meeting_id',
            help='Meeting ID to export'
        )

        # Content options
        parser.add_argument(
            '--no-transcript',
            action='store_true',
            help='Exclude transcript from export'
        )

        parser.add_argument(
            '--no-metadata',
            action='store_true',
            help='Exclude metadata from export'
        )

        parser.add_argument(
            '--no-participants',
            action='store_true',
            help='Exclude participants from export'
        )

        parser.add_argument(
            '--no-summary',
            action='store_true',
            help='Exclude AI summary from export'
        )

        parser.add_argument(
            '--no-notes',
            action='store_true',
            help='Exclude human notes from export'
        )

        parser.add_argument(
            '--no-tags',
            action='store_true',
            help='Exclude tags from export'
        )

        # Transcript formatting options
        parser.add_argument(
            '--no-speakers',
            action='store_true',
            help='Hide speaker names in transcript'
        )

        parser.add_argument(
            '--timestamps',
            action='store_true',
            help='Include timestamps in transcript'
        )

        # Output options
        parser.add_argument(
            '--output', '-o',
            type=str,
            help='Output file path (default: stdout)'
        )

        parser.add_argument(
            '--title',
            type=str,
            help='Override meeting title in export'
        )

    def _find_meeting(self, meeting_id: str) -> Optional[Meeting]:
        """
        Find a meeting by ID.

        Args:
            meeting_id: Meeting ID to search for

        Returns:
            Optional[Meeting]: Found meeting or None
        """
        meeting_data = self.parser.get_meeting_by_id(meeting_id)
        if meeting_data:
            return Meeting(meeting_data)

        # Try partial ID match
        all_meetings = self.parser.get_meetings()
        for data in all_meetings:
            meeting = Meeting(data)
            if meeting.id and meeting.id.startswith(meeting_id):
                return meeting

        return None

    def _export_meeting(self, meeting: Meeting) -> str:
        """
        Export meeting to markdown format.

        Args:
            meeting: Meeting to export

        Returns:
            str: Markdown content
        """
        # Override title if specified
        if self.args.title:
            # Create a copy of the meeting data with custom title
            meeting_data = meeting.raw_data.copy()
            meeting_data['title'] = self.args.title
            meeting = Meeting(meeting_data)

        # Determine what to include
        include_transcript = not self.args.no_transcript
        include_metadata = not self.args.no_metadata
        include_participants = not self.args.no_participants
        include_summary = not self.args.no_summary
        include_notes = not self.args.no_notes
        include_tags = not self.args.no_tags
        include_speakers = not self.args.no_speakers
        include_timestamps = self.args.timestamps

        return export_meeting_to_markdown(
            meeting,
            include_transcript=include_transcript,
            include_metadata=include_metadata,
            include_participants=include_participants,
            include_summary=include_summary,
            include_notes=include_notes,
            include_tags=include_tags,
            include_speakers=include_speakers,
            include_timestamps=include_timestamps
        )

    def _write_output(self, content: str) -> None:
        """
        Write content to output destination.

        Args:
            content: Content to write
        """
        if self.args.output:
            try:
                with open(self.args.output, 'w', encoding='utf-8') as f:
                    f.write(content)
                if self.args.verbose:
                    print_info(f"Exported to: {self.args.output}", file=sys.stderr)
            except Exception as e:
                print_error(f"Error writing to file {self.args.output}: {e}")
                raise
        else:
            # Write to stdout
            print(content)

    def execute(self) -> int:
        """
        Execute the export command.

        Returns:
            int: Exit code (0 for success)
        """
        try:
            # Find the meeting
            meeting = self._find_meeting(self.args.meeting_id)
            if not meeting:
                print_error(f"Meeting not found: {self.args.meeting_id}")
                return 1

            if self.args.verbose:
                title = meeting.title or "Untitled Meeting"
                print_info(f"Exporting meeting: {title}", file=sys.stderr)

            # Export to markdown
            markdown_content = self._export_meeting(meeting)

            # Write output
            self._write_output(markdown_content)

            return 0

        except Exception as e:
            print_error(f"Error exporting meeting: {e}")
            if self.args.verbose:
                import traceback
                traceback.print_exc()
            return 1