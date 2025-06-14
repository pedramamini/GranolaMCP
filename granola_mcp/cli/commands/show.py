"""
Show command implementation for GranolaMCP CLI.

Provides functionality to display detailed information about a specific meeting
including metadata, participants, summary, and transcript.
"""

import argparse
from typing import Optional
from ...core.parser import GranolaParser
from ...core.meeting import Meeting
from ..formatters.colors import (
    Colors, colorize, format_duration, print_error, print_info,
    print_header, print_subheader, muted, bold
)
from ..formatters.table import print_key_value_pairs, print_section, print_list_items


class ShowCommand:
    """Command to show detailed meeting information."""

    def __init__(self, parser: GranolaParser, args: argparse.Namespace):
        """
        Initialize the show command.

        Args:
            parser: GranolaParser instance
            args: Parsed command line arguments
        """
        self.parser = parser
        self.args = args

    @staticmethod
    def add_arguments(parser: argparse.ArgumentParser) -> None:
        """
        Add arguments for the show command.

        Args:
            parser: Argument parser to add arguments to
        """
        parser.add_argument(
            'meeting_id',
            help='Meeting ID to display'
        )

        # Content options
        parser.add_argument(
            '--transcript',
            action='store_true',
            help='Include full transcript in output'
        )

        parser.add_argument(
            '--summary',
            action='store_true',
            help='Include meeting summary/notes'
        )

        parser.add_argument(
            '--metadata',
            action='store_true',
            help='Show detailed metadata'
        )

        parser.add_argument(
            '--all',
            action='store_true',
            help='Show all available information (equivalent to --transcript --summary --metadata)'
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

        parser.add_argument(
            '--speaker',
            type=str,
            help='Show transcript for specific speaker only'
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

    def _show_basic_info(self, meeting: Meeting) -> None:
        """
        Show basic meeting information.

        Args:
            meeting: Meeting to display
        """
        title = meeting.title or "Untitled Meeting"
        print_header(title)
        print()

        # Basic details
        details = []

        if meeting.id:
            details.append(("Meeting ID", meeting.id))

        if meeting.start_time:
            details.append(("Date & Time", meeting.start_time.strftime("%Y-%m-%d %H:%M:%S %Z")))

        if meeting.end_time:
            details.append(("End Time", meeting.end_time.strftime("%Y-%m-%d %H:%M:%S %Z")))

        if meeting.duration:
            duration_str = format_duration(meeting.duration.total_seconds())
            # Remove ANSI codes for clean display
            import re
            ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
            duration_str = ansi_escape.sub('', duration_str)
            details.append(("Duration", duration_str))

        participants = meeting.participants
        if participants:
            details.append(("Participants", f"{len(participants)} attendees"))

        if meeting.has_transcript():
            details.append(("Transcript", "Available"))
        else:
            details.append(("Transcript", muted("Not available")))

        if details:
            print_key_value_pairs(details)

    def _show_participants(self, meeting: Meeting) -> None:
        """
        Show meeting participants.

        Args:
            meeting: Meeting to display
        """
        participants = meeting.participants
        if not participants:
            return

        print_section("Participants")
        print_list_items(participants)

    def _show_summary(self, meeting: Meeting) -> None:
        """
        Show meeting summary/notes.

        Args:
            meeting: Meeting to display
        """
        summary = meeting.summary
        if not summary:
            return

        print_section("Summary")
        print(summary)

    def _show_tags(self, meeting: Meeting) -> None:
        """
        Show meeting tags.

        Args:
            meeting: Meeting to display
        """
        tags = meeting.tags
        if not tags:
            return

        print_section("Tags")
        tag_items = [colorize(tag, Colors.CYAN) for tag in tags]
        print(" ".join(tag_items))

    def _show_metadata(self, meeting: Meeting) -> None:
        """
        Show detailed metadata.

        Args:
            meeting: Meeting to display
        """
        print_section("Detailed Metadata")

        # Get raw data keys
        raw_data = meeting.raw_data
        metadata_items = []

        # Show all available fields
        for key, value in raw_data.items():
            if key not in ['transcript', 'transcription', 'content', 'text']:
                if isinstance(value, (str, int, float, bool)):
                    metadata_items.append((key, str(value)))
                elif isinstance(value, list):
                    metadata_items.append((key, f"List with {len(value)} items"))
                elif isinstance(value, dict):
                    metadata_items.append((key, f"Object with {len(value)} fields"))
                else:
                    metadata_items.append((key, type(value).__name__))

        if metadata_items:
            print_key_value_pairs(metadata_items)

    def _show_transcript(self, meeting: Meeting) -> None:
        """
        Show meeting transcript.

        Args:
            meeting: Meeting to display
        """
        transcript = meeting.transcript
        if not transcript:
            print_info("No transcript available for this meeting.")
            return

        print_section("Transcript")

        segments = transcript.segments
        if not segments:
            # Show full text if no segments
            print(transcript.full_text)
            return

        # Filter by speaker if requested
        if self.args.speaker:
            segments = [s for s in segments if s.speaker and
                       self.args.speaker.lower() in s.speaker.lower()]
            if not segments:
                print_info(f"No transcript segments found for speaker: {self.args.speaker}")
                return

        # Display segments
        current_speaker = None
        show_speakers = not self.args.no_speakers

        for segment in segments:
            text = segment.text.strip()
            if not text:
                continue

            speaker = segment.speaker

            # Show speaker header if changed and speakers are enabled
            if show_speakers and speaker and speaker != current_speaker:
                if current_speaker is not None:
                    print()  # Add spacing between speakers
                print(bold(f"{speaker}:"))
                current_speaker = speaker

            # Format timestamp if requested
            timestamp_prefix = ""
            if self.args.timestamps and segment.start_time is not None:
                minutes = int(segment.start_time // 60)
                seconds = int(segment.start_time % 60)
                timestamp_prefix = muted(f"[{minutes:02d}:{seconds:02d}] ")

            # Display the text
            if show_speakers and speaker:
                print(f"  {timestamp_prefix}{text}")
            else:
                speaker_name = speaker or "Unknown"
                print(f"{timestamp_prefix}{bold(speaker_name + ':')} {text}")

    def execute(self) -> int:
        """
        Execute the show command.

        Returns:
            int: Exit code (0 for success)
        """
        try:
            # Find the meeting
            meeting = self._find_meeting(self.args.meeting_id)
            if not meeting:
                print_error(f"Meeting not found: {self.args.meeting_id}")
                return 1

            # Determine what to show
            show_transcript = self.args.transcript or self.args.all
            show_summary = self.args.summary or self.args.all
            show_metadata = self.args.metadata or self.args.all

            # Show basic information
            self._show_basic_info(meeting)

            # Show participants
            self._show_participants(meeting)

            # Show summary (always show if available by default)
            self._show_summary(meeting)

            # Show tags
            self._show_tags(meeting)

            # Show detailed metadata
            if show_metadata:
                self._show_metadata(meeting)

            # Show transcript
            if show_transcript:
                self._show_transcript(meeting)

            return 0

        except Exception as e:
            print_error(f"Error showing meeting: {e}")
            if self.args.verbose:
                import traceback
                traceback.print_exc()
            return 1