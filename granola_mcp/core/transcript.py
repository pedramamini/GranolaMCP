"""
Transcript data model for GranolaMCP.

Provides the Transcript class for representing and working with meeting
transcript data from Granola.ai.
"""

import datetime
from typing import Dict, Any, List, Optional, Union
from .timezone_utils import convert_utc_to_cst


class TranscriptSegment:
    """
    Represents a single segment of transcript text with speaker and timing information.
    """

    def __init__(self, segment_data: Dict[str, Any]):
        """
        Initialize a TranscriptSegment from raw segment data.

        Args:
            segment_data: Raw segment data dictionary
        """
        self._data = segment_data

    @property
    def text(self) -> str:
        """Get the segment text."""
        # Try different possible text fields
        for text_field in ['text', 'content', 'transcript', 'message']:
            if text_field in self._data:
                return str(self._data[text_field])
        return ""

    @property
    def speaker(self) -> Optional[str]:
        """Get the speaker name."""
        # Try different possible speaker fields, including Granola's source field
        for speaker_field in ['speaker', 'user', 'name', 'participant', 'source']:
            if speaker_field in self._data:
                return str(self._data[speaker_field])
        return None

    @property
    def timestamp(self) -> Optional[datetime.datetime]:
        """Get the segment timestamp in CST."""
        # Try different possible timestamp fields, including Granola's absolute timestamps
        for time_field in ['timestamp', 'time', 'start_timestamp', 'created_at']:
            if time_field in self._data:
                try:
                    return convert_utc_to_cst(self._data[time_field])
                except (ValueError, TypeError):
                    continue
        return None

    @property
    def start_time(self) -> Optional[float]:
        """Get the segment start time in seconds from meeting start."""
        # Try different possible start time fields, including Granola's startSec
        for time_field in ['start_time', 'startTime', 'startSec', 'offset', 'start']:
            if time_field in self._data:
                try:
                    return float(self._data[time_field])
                except (ValueError, TypeError):
                    continue
        return None

    @property
    def end_time(self) -> Optional[float]:
        """Get the segment end time in seconds from meeting start."""
        # Try different possible end time fields
        for time_field in ['end_time', 'endTime', 'end']:
            if time_field in self._data:
                try:
                    return float(self._data[time_field])
                except (ValueError, TypeError):
                    continue
        return None

    @property
    def duration(self) -> Optional[float]:
        """Get the segment duration in seconds."""
        start = self.start_time
        end = self.end_time

        if start is not None and end is not None:
            return end - start

        # Try to get duration directly
        if 'duration' in self._data:
            try:
                return float(self._data['duration'])
            except (ValueError, TypeError):
                pass

        return None

    def to_dict(self) -> Dict[str, Any]:
        """Convert segment to dictionary."""
        return {
            'text': self.text,
            'speaker': self.speaker,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'duration': self.duration,
        }

    def __str__(self) -> str:
        """String representation of the segment."""
        speaker = self.speaker or "Unknown"
        return f"[{speaker}]: {self.text}"


class Transcript:
    """
    Represents a complete meeting transcript with segments and metadata.
    """

    def __init__(self, transcript_data: Union[Dict[str, Any], List[Dict[str, Any]], str]):
        """
        Initialize a Transcript from raw transcript data.

        Args:
            transcript_data: Raw transcript data (dict, list, or string)
        """
        self._raw_data = transcript_data
        self._segments: Optional[List[TranscriptSegment]] = None
        self._full_text: Optional[str] = None

    @property
    def segments(self) -> List[TranscriptSegment]:
        """Get the transcript segments."""
        if self._segments is None:
            self._segments = self._parse_segments()
        return self._segments

    def _parse_segments(self) -> List[TranscriptSegment]:
        """Parse segments from raw transcript data."""
        segments = []

        if isinstance(self._raw_data, str):
            # Simple text transcript - create a single segment
            segments.append(TranscriptSegment({'text': self._raw_data}))
        elif isinstance(self._raw_data, list):
            # List of segments (Granola format when transcript is directly a list)
            for item in self._raw_data:
                if isinstance(item, dict):
                    # Pass the raw data directly to TranscriptSegment for proper parsing
                    # The TranscriptSegment class will handle the field mapping
                    segments.append(TranscriptSegment(item))
                elif isinstance(item, str):
                    segments.append(TranscriptSegment({'text': item}))
        elif isinstance(self._raw_data, dict):
            # Dictionary containing segments or text
            # Try Granola format first (chunks field)
            if 'chunks' in self._raw_data and isinstance(self._raw_data['chunks'], list):
                for chunk in self._raw_data['chunks']:
                    if isinstance(chunk, dict):
                        segment_data = {
                            'text': chunk.get('text', ''),
                            'speaker': chunk.get('speaker', 'Unknown'),
                            'start_time': chunk.get('startSec', 0)
                        }
                        segments.append(TranscriptSegment(segment_data))
            else:
                # Try to find segments in other possible fields
                for segments_field in ['segments', 'items', 'entries', 'messages']:
                    if segments_field in self._raw_data:
                        segment_data = self._raw_data[segments_field]
                        if isinstance(segment_data, list):
                            for item in segment_data:
                                if isinstance(item, dict):
                                    segments.append(TranscriptSegment(item))
                        break

                # If no segments found, treat the whole dict as a single segment
                if not segments:
                    segments.append(TranscriptSegment(self._raw_data))

        return segments

    @property
    def full_text(self) -> str:
        """Get the complete transcript text."""
        if self._full_text is None:
            self._full_text = self._build_full_text()
        return self._full_text

    def _build_full_text(self) -> str:
        """Build the complete transcript text from segments."""
        if isinstance(self._raw_data, str):
            return self._raw_data

        # Combine all segment texts
        texts = []
        for segment in self.segments:
            if segment.text.strip():
                texts.append(segment.text.strip())

        return '\n'.join(texts)

    @property
    def speakers(self) -> List[str]:
        """Get unique speakers in the transcript."""
        speakers = set()
        for segment in self.segments:
            if segment.speaker:
                speakers.add(segment.speaker)
        return sorted(list(speakers))

    @property
    def word_count(self) -> int:
        """Get the total word count of the transcript."""
        return len(self.full_text.split())

    @property
    def duration(self) -> Optional[float]:
        """Get the total duration of the transcript in seconds."""
        segments = self.segments
        if not segments:
            return None

        # Try relative timestamps first (more accurate for duration)
        max_end_time = None
        for segment in segments:
            if segment.end_time is not None:
                if max_end_time is None or segment.end_time > max_end_time:
                    max_end_time = segment.end_time

        if max_end_time is not None:
            return max_end_time
        
        # Fallback: try to calculate from absolute timestamps
        segments_with_timestamps = [s for s in segments if s.timestamp is not None]
        if len(segments_with_timestamps) >= 2:
            first_timestamp = min(s.timestamp for s in segments_with_timestamps)
            last_timestamp = max(s.timestamp for s in segments_with_timestamps)
            duration_timedelta = last_timestamp - first_timestamp
            return duration_timedelta.total_seconds()

        return None

    def get_segments_by_speaker(self, speaker: str) -> List[TranscriptSegment]:
        """
        Get all segments for a specific speaker.

        Args:
            speaker: Speaker name to filter by

        Returns:
            List[TranscriptSegment]: Segments for the speaker
        """
        return [segment for segment in self.segments if segment.speaker == speaker]

    def get_segments_in_time_range(self, start_time: float, end_time: float) -> List[TranscriptSegment]:
        """
        Get segments within a specific time range.

        Args:
            start_time: Start time in seconds
            end_time: End time in seconds

        Returns:
            List[TranscriptSegment]: Segments in the time range
        """
        segments = []
        for segment in self.segments:
            seg_start = segment.start_time
            seg_end = segment.end_time

            if seg_start is not None and seg_end is not None:
                # Check if segment overlaps with the time range
                if seg_start <= end_time and seg_end >= start_time:
                    segments.append(segment)

        return segments

    def search_text(self, query: str, case_sensitive: bool = False) -> List[TranscriptSegment]:
        """
        Search for text in the transcript.

        Args:
            query: Text to search for
            case_sensitive: Whether search should be case sensitive

        Returns:
            List[TranscriptSegment]: Segments containing the query
        """
        if not case_sensitive:
            query = query.lower()

        matching_segments = []
        for segment in self.segments:
            text = segment.text if case_sensitive else segment.text.lower()
            if query in text:
                matching_segments.append(segment)

        return matching_segments

    def to_dict(self) -> Dict[str, Any]:
        """Convert transcript to dictionary."""
        return {
            'full_text': self.full_text,
            'word_count': self.word_count,
            'speakers': self.speakers,
            'duration': self.duration,
            'segment_count': len(self.segments),
            'segments': [segment.to_dict() for segment in self.segments],
        }

    def __str__(self) -> str:
        """String representation of the transcript."""
        return self.full_text

    def __len__(self) -> int:
        """Get the number of segments in the transcript."""
        return len(self.segments)