"""
Markdown formatting utilities for GranolaMCP CLI.

Provides functions for exporting meeting data to clean markdown format
suitable for documentation and sharing.
"""

import datetime
from typing import List, Optional, Dict, Any
from ..formatters.colors import format_duration
from ...core.meeting import Meeting
from ...core.transcript import TranscriptSegment


def escape_markdown(text: str) -> str:
    """
    Escape special markdown characters in text.

    Args:
        text: Text to escape

    Returns:
        str: Escaped text
    """
    if not text:
        return ""

    # Escape markdown special characters
    special_chars = ['\\', '`', '*', '_', '{', '}', '[', ']', '(', ')', '#', '+', '-', '.', '!']
    escaped_text = text

    for char in special_chars:
        escaped_text = escaped_text.replace(char, f'\\{char}')

    return escaped_text


def format_meeting_header(meeting: Meeting) -> str:
    """
    Format meeting header in markdown.

    Args:
        meeting: Meeting object

    Returns:
        str: Formatted markdown header
    """
    lines = []

    # Main title
    title = meeting.title or "Untitled Meeting"
    lines.append(f"# {escape_markdown(title)}")
    lines.append("")

    return "\n".join(lines)


def format_meeting_metadata(meeting: Meeting) -> str:
    """
    Format meeting metadata in markdown.

    Args:
        meeting: Meeting object

    Returns:
        str: Formatted markdown metadata
    """
    lines = []
    lines.append("## Meeting Information")
    lines.append("")

    # Meeting details table
    metadata_items = []

    if meeting.id:
        metadata_items.append(("Meeting ID", f"`{meeting.id}`"))

    if meeting.start_time:
        metadata_items.append(("Date & Time", meeting.start_time.strftime("%Y-%m-%d %H:%M:%S %Z")))

    if meeting.duration:
        duration_str = format_duration(meeting.duration.total_seconds())
        # Remove ANSI codes for markdown
        import re
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        duration_str = ansi_escape.sub('', duration_str)
        metadata_items.append(("Duration", duration_str))

    participants = meeting.participants
    if participants:
        metadata_items.append(("Participants", f"{len(participants)} attendees"))

    # Format as markdown table
    if metadata_items:
        lines.append("| Field | Value |")
        lines.append("|-------|-------|")
        for key, value in metadata_items:
            lines.append(f"| {key} | {value} |")
        lines.append("")

    return "\n".join(lines)


def format_participants_section(meeting: Meeting) -> str:
    """
    Format participants section in markdown.

    Args:
        meeting: Meeting object

    Returns:
        str: Formatted markdown participants section
    """
    participants = meeting.participants
    if not participants:
        return ""

    lines = []
    lines.append("## Participants")
    lines.append("")

    for participant in participants:
        lines.append(f"- {escape_markdown(participant)}")

    lines.append("")
    return "\n".join(lines)


def format_summary_section(meeting: Meeting) -> str:
    """
    Format AI summary section in markdown.

    Args:
        meeting: Meeting object

    Returns:
        str: Formatted markdown AI summary section
    """
    summary = meeting.summary
    if not summary:
        return ""

    lines = []
    lines.append("## AI Summary")
    lines.append("")
    lines.append(escape_markdown(summary))
    lines.append("")

    return "\n".join(lines)


def format_notes_section(meeting: Meeting) -> str:
    """
    Format human notes section in markdown.

    Args:
        meeting: Meeting object

    Returns:
        str: Formatted markdown human notes section
    """
    notes = meeting.human_notes
    if not notes:
        return ""

    lines = []
    lines.append("## Human Notes")
    lines.append("")
    lines.append(escape_markdown(notes))
    lines.append("")

    return "\n".join(lines)


def format_transcript_section(meeting: Meeting, include_speakers: bool = True,
                            include_timestamps: bool = False) -> str:
    """
    Format transcript section in markdown.

    Args:
        meeting: Meeting object
        include_speakers: Whether to include speaker names
        include_timestamps: Whether to include timestamps

    Returns:
        str: Formatted markdown transcript section
    """
    transcript = meeting.transcript
    if not transcript:
        return ""

    lines = []
    lines.append("## Transcript")
    lines.append("")

    segments = transcript.segments
    if not segments:
        # Fallback to full text if no segments
        lines.append("```")
        lines.append(escape_markdown(transcript.full_text))
        lines.append("```")
    else:
        # Format segments
        current_speaker = None

        for segment in segments:
            speaker = segment.speaker
            text = segment.text.strip()

            if not text:
                continue

            # Add speaker header if changed and speakers are included
            if include_speakers and speaker and speaker != current_speaker:
                if current_speaker is not None:
                    lines.append("")  # Add spacing between speakers
                lines.append(f"**{escape_markdown(speaker)}:**")
                lines.append("")
                current_speaker = speaker

            # Add timestamp if requested
            timestamp_prefix = ""
            if include_timestamps and segment.start_time is not None:
                minutes = int(segment.start_time // 60)
                seconds = int(segment.start_time % 60)
                timestamp_prefix = f"*[{minutes:02d}:{seconds:02d}]* "

            # Add the text
            if include_speakers and speaker:
                lines.append(f"{timestamp_prefix}{escape_markdown(text)}")
            else:
                lines.append(f"{timestamp_prefix}**{escape_markdown(speaker or 'Unknown')}:** {escape_markdown(text)}")

            lines.append("")

    return "\n".join(lines)


def format_tags_section(meeting: Meeting) -> str:
    """
    Format tags section in markdown.

    Args:
        meeting: Meeting object

    Returns:
        str: Formatted markdown tags section
    """
    tags = meeting.tags
    if not tags:
        return ""

    lines = []
    lines.append("## Tags")
    lines.append("")

    tag_items = [f"`{escape_markdown(tag)}`" for tag in tags]
    lines.append(" ".join(tag_items))
    lines.append("")

    return "\n".join(lines)


def export_meeting_to_markdown(meeting: Meeting, include_transcript: bool = True,
                              include_metadata: bool = True, include_participants: bool = True,
                              include_summary: bool = True, include_notes: bool = True,
                              include_tags: bool = True, include_speakers: bool = True,
                              include_timestamps: bool = False) -> str:
    """
    Export a complete meeting to markdown format.

    Args:
        meeting: Meeting object to export
        include_transcript: Whether to include transcript
        include_metadata: Whether to include metadata
        include_participants: Whether to include participants
        include_summary: Whether to include AI summary
        include_notes: Whether to include human notes
        include_tags: Whether to include tags
        include_speakers: Whether to include speaker names in transcript
        include_timestamps: Whether to include timestamps in transcript

    Returns:
        str: Complete markdown document
    """
    sections = []

    # Header
    sections.append(format_meeting_header(meeting))

    # Metadata
    if include_metadata:
        metadata_section = format_meeting_metadata(meeting)
        if metadata_section.strip():
            sections.append(metadata_section)

    # Participants
    if include_participants:
        participants_section = format_participants_section(meeting)
        if participants_section.strip():
            sections.append(participants_section)

    # Human Notes
    if include_notes:
        notes_section = format_notes_section(meeting)
        if notes_section.strip():
            sections.append(notes_section)

    # AI Summary
    if include_summary:
        summary_section = format_summary_section(meeting)
        if summary_section.strip():
            sections.append(summary_section)

    # Tags
    if include_tags:
        tags_section = format_tags_section(meeting)
        if tags_section.strip():
            sections.append(tags_section)

    # Transcript
    if include_transcript:
        transcript_section = format_transcript_section(
            meeting, include_speakers, include_timestamps
        )
        if transcript_section.strip():
            sections.append(transcript_section)

    # Add footer
    sections.append("---")
    sections.append(f"*Exported on {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")

    return "\n".join(sections)


def create_meeting_summary_table(meetings: List[Meeting]) -> str:
    """
    Create a markdown table summarizing multiple meetings.

    Args:
        meetings: List of meetings to summarize

    Returns:
        str: Markdown table
    """
    if not meetings:
        return "No meetings found."

    lines = []
    lines.append("| Meeting | Date | Duration | Participants |")
    lines.append("|---------|------|----------|--------------|")

    for meeting in meetings:
        title = escape_markdown(meeting.title or "Untitled")

        date_str = "Unknown"
        if meeting.start_time:
            date_str = meeting.start_time.strftime("%Y-%m-%d")

        duration_str = "Unknown"
        if meeting.duration:
            duration_str = format_duration(meeting.duration.total_seconds())
            # Remove ANSI codes
            import re
            ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
            duration_str = ansi_escape.sub('', duration_str)

        participant_count = len(meeting.participants)

        lines.append(f"| {title} | {date_str} | {duration_str} | {participant_count} |")

    return "\n".join(lines)