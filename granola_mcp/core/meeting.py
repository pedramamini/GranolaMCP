"""
Meeting data model for GranolaMCP.

Provides the Meeting class for representing and working with individual
Granola.ai meeting objects.
"""

import datetime
from typing import Dict, Any, List, Optional
from .timezone_utils import convert_utc_to_cst
from .transcript import Transcript


class Meeting:
    """
    Represents a single Granola.ai meeting with its metadata and content.
    """

    def __init__(self, meeting_data: Dict[str, Any]):
        """
        Initialize a Meeting object from raw meeting data.

        Args:
            meeting_data: Raw meeting data dictionary from cache
        """
        self._data = meeting_data
        self._transcript: Optional[Transcript] = None

    @property
    def id(self) -> Optional[str]:
        """Get the meeting ID."""
        # Try different possible ID fields
        for id_field in ['id', 'meeting_id', 'session_id', 'uuid']:
            if id_field in self._data:
                return str(self._data[id_field])
        return None

    @property
    def title(self) -> Optional[str]:
        """Get the meeting title."""
        # Try different possible title fields
        for title_field in ['title', 'name', 'subject', 'meeting_name', 'summary']:
            if title_field in self._data:
                return str(self._data[title_field])
        return None

    @property
    def start_time(self) -> Optional[datetime.datetime]:
        """Get the meeting start time in CST."""
        # Try different possible start time fields
        for time_field in ['start_time', 'startTime', 'created_at', 'timestamp', 'date']:
            if time_field in self._data:
                try:
                    return convert_utc_to_cst(self._data[time_field])
                except (ValueError, TypeError):
                    continue

        # Handle Google Calendar format: start.dateTime
        if 'start' in self._data and isinstance(self._data['start'], dict):
            start_data = self._data['start']
            if 'dateTime' in start_data:
                try:
                    return convert_utc_to_cst(start_data['dateTime'])
                except (ValueError, TypeError):
                    pass

        return None

    @property
    def end_time(self) -> Optional[datetime.datetime]:
        """Get the meeting end time in CST."""
        # Try different possible end time fields
        for time_field in ['end_time', 'endTime', 'finished_at']:
            if time_field in self._data:
                try:
                    return convert_utc_to_cst(self._data[time_field])
                except (ValueError, TypeError):
                    continue

        # Handle Google Calendar format: end.dateTime
        if 'end' in self._data and isinstance(self._data['end'], dict):
            end_data = self._data['end']
            if 'dateTime' in end_data:
                try:
                    return convert_utc_to_cst(end_data['dateTime'])
                except (ValueError, TypeError):
                    pass

        return None

    @property
    def duration(self) -> Optional[datetime.timedelta]:
        """Get the meeting duration."""
        start = self.start_time
        end = self.end_time

        if start and end:
            return end - start

        # Try to get duration directly from data
        for duration_field in ['duration', 'length', 'duration_seconds']:
            if duration_field in self._data:
                try:
                    seconds = float(self._data[duration_field])
                    return datetime.timedelta(seconds=seconds)
                except (ValueError, TypeError):
                    continue

        return None

    @property
    def participants(self) -> List[str]:
        """Get the list of meeting participants."""
        participants = []

        # Try different possible participant fields
        for participant_field in ['participants', 'attendees', 'users', 'members']:
            if participant_field in self._data:
                participant_data = self._data[participant_field]

                if isinstance(participant_data, list):
                    for participant in participant_data:
                        if isinstance(participant, str):
                            participants.append(participant)
                        elif isinstance(participant, dict):
                            # Try to extract name from participant object
                            for name_field in ['name', 'display_name', 'email', 'username']:
                                if name_field in participant:
                                    participants.append(str(participant[name_field]))
                                    break
                break

        return participants

    @property
    def transcript(self) -> Optional[Transcript]:
        """Get the meeting transcript."""
        if self._transcript is None:
            # Try to find transcript data
            transcript_data = None

            for transcript_field in ['transcript', 'transcription', 'content', 'text']:
                if transcript_field in self._data:
                    transcript_data = self._data[transcript_field]
                    break

            if transcript_data:
                self._transcript = Transcript(transcript_data)

        return self._transcript

    @property
    def summary(self) -> Optional[str]:
        """Get the meeting summary."""
        # Try different possible summary fields
        for summary_field in ['summary', 'description', 'notes', 'overview']:
            if summary_field in self._data:
                return str(self._data[summary_field])
        return None

    @property
    def tags(self) -> List[str]:
        """Get the meeting tags."""
        tags = []

        for tag_field in ['tags', 'labels', 'categories']:
            if tag_field in self._data:
                tag_data = self._data[tag_field]

                if isinstance(tag_data, list):
                    tags.extend([str(tag) for tag in tag_data])
                elif isinstance(tag_data, str):
                    # Handle comma-separated tags
                    tags.extend([tag.strip() for tag in tag_data.split(',')])
                break

        return tags

    @property
    def raw_data(self) -> Dict[str, Any]:
        """Get the raw meeting data."""
        return self._data.copy()

    def get_field(self, field_name: str, default: Any = None) -> Any:
        """
        Get a specific field from the meeting data.

        Args:
            field_name: Name of the field to retrieve
            default: Default value if field not found

        Returns:
            Any: Field value or default
        """
        return self._data.get(field_name, default)

    def has_transcript(self) -> bool:
        """Check if the meeting has transcript data."""
        return self.transcript is not None

    def is_in_date_range(self, start_date: datetime.datetime, end_date: datetime.datetime) -> bool:
        """
        Check if the meeting falls within a date range.

        Args:
            start_date: Start of date range
            end_date: End of date range

        Returns:
            bool: True if meeting is in range
        """
        meeting_time = self.start_time
        if meeting_time is None:
            return False

        return start_date <= meeting_time <= end_date

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert meeting to a dictionary with standardized fields.

        Returns:
            Dict[str, Any]: Standardized meeting dictionary
        """
        return {
            'id': self.id,
            'title': self.title,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'duration_seconds': self.duration.total_seconds() if self.duration else None,
            'participants': self.participants,
            'summary': self.summary,
            'tags': self.tags,
            'has_transcript': self.has_transcript(),
        }

    def __str__(self) -> str:
        """String representation of the meeting."""
        title = self.title or "Untitled Meeting"
        start_time = self.start_time.strftime("%Y-%m-%d %H:%M") if self.start_time else "Unknown time"
        return f"Meeting: {title} ({start_time})"

    def __repr__(self) -> str:
        """Detailed string representation of the meeting."""
        return f"Meeting(id={self.id}, title='{self.title}', start_time={self.start_time})"