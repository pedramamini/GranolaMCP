"""
MCP tools implementation for GranolaMCP.

Provides all the MCP tools for accessing and analyzing Granola meeting data,
including search, retrieval, statistics, and export functionality.
"""

import json
import datetime
import statistics
from collections import defaultdict, Counter
from typing import Dict, Any, List, Optional, Union
from ..core.parser import GranolaParser, GranolaParseError
from ..core.meeting import Meeting
from ..utils.date_parser import parse_date, get_date_range
from ..cli.formatters.markdown import export_meeting_to_markdown


class MCPToolError(Exception):
    """Custom exception for MCP tool errors."""
    pass


class MCPTools:
    """
    Collection of MCP tools for accessing Granola meeting data.

    Provides comprehensive access to meeting data, analytics, and export
    functionality optimized for LLM consumption.
    """

    def __init__(self, parser: GranolaParser):
        """
        Initialize MCP tools with a parser instance.

        Args:
            parser: GranolaParser instance for data access
        """
        self.parser = parser
        self._meetings_cache: Optional[List[Meeting]] = None

    def _get_meetings(self, force_reload: bool = False) -> List[Meeting]:
        """
        Get all meetings, with caching for performance.

        Args:
            force_reload: Force reload from cache file

        Returns:
            List[Meeting]: All available meetings
        """
        if self._meetings_cache is None or force_reload:
            try:
                meeting_data = self.parser.get_meetings()
                self._meetings_cache = [Meeting(data) for data in meeting_data]
            except Exception as e:
                raise MCPToolError(f"Failed to load meetings: {e}")

        return self._meetings_cache

    def _filter_meetings_by_date(self, meetings: List[Meeting],
                                from_date: Optional[str] = None,
                                to_date: Optional[str] = None) -> List[Meeting]:
        """
        Filter meetings by date range.

        Args:
            meetings: List of meetings to filter
            from_date: Start date (ISO format or relative like '30d')
            to_date: End date (ISO format or relative like '1d')

        Returns:
            List[Meeting]: Filtered meetings
        """
        if not from_date and not to_date:
            return meetings

        try:
            if from_date and to_date:
                start_date, end_date = get_date_range(from_date, to_date)
            elif from_date:
                start_date = parse_date(from_date)
                end_date = datetime.datetime.now(start_date.tzinfo)
            else:
                # Only to_date specified
                if to_date:
                    end_date = parse_date(to_date)
                    start_date = datetime.datetime.min.replace(tzinfo=end_date.tzinfo)
                else:
                    return meetings

            filtered_meetings = []
            for meeting in meetings:
                if meeting.start_time and start_date <= meeting.start_time <= end_date:
                    filtered_meetings.append(meeting)

            return filtered_meetings

        except ValueError as e:
            raise MCPToolError(f"Invalid date format: {e}")

    def _filter_meetings_by_participant(self, meetings: List[Meeting],
                                      participant: str) -> List[Meeting]:
        """
        Filter meetings by participant.

        Args:
            meetings: List of meetings to filter
            participant: Participant email or name to filter by

        Returns:
            List[Meeting]: Meetings with the specified participant
        """
        filtered_meetings = []
        participant_lower = participant.lower()

        for meeting in meetings:
            for p in meeting.participants:
                if participant_lower in p.lower():
                    filtered_meetings.append(meeting)
                    break

        return filtered_meetings

    def _search_meetings_by_query(self, meetings: List[Meeting],
                                query: str) -> List[Meeting]:
        """
        Search meetings by text query in title and content.

        Args:
            meetings: List of meetings to search
            query: Search query

        Returns:
            List[Meeting]: Meetings matching the query
        """
        matching_meetings = []
        query_lower = query.lower()

        for meeting in meetings:
            # Search in title
            if meeting.title and query_lower in meeting.title.lower():
                matching_meetings.append(meeting)
                continue

            # Search in summary
            if meeting.summary and query_lower in meeting.summary.lower():
                matching_meetings.append(meeting)
                continue

            # Search in transcript
            if meeting.has_transcript() and meeting.transcript:
                if query_lower in meeting.transcript.full_text.lower():
                    matching_meetings.append(meeting)
                    continue

        return matching_meetings

    def search_meetings(self, query: Optional[str] = None,
                       from_date: Optional[str] = None,
                       to_date: Optional[str] = None,
                       participant: Optional[str] = None,
                       limit: Optional[int] = None) -> Dict[str, Any]:
        """
        Search meetings with flexible filters.

        Args:
            query: Text search in title/content
            from_date: Start date filter
            to_date: End date filter
            participant: Participant filter
            limit: Maximum number of results

        Returns:
            Dict containing search results
        """
        try:
            meetings = self._get_meetings()

            # Apply filters
            if from_date or to_date:
                meetings = self._filter_meetings_by_date(meetings, from_date, to_date)

            if participant:
                meetings = self._filter_meetings_by_participant(meetings, participant)

            if query:
                meetings = self._search_meetings_by_query(meetings, query)

            # Apply limit
            if limit and limit > 0:
                meetings = meetings[:limit]

            # Format results
            results = []
            for meeting in meetings:
                result = {
                    "id": meeting.id,
                    "title": meeting.title,
                    "start_time": meeting.start_time.isoformat() if meeting.start_time else None,
                    "duration_minutes": int(meeting.duration.total_seconds() / 60) if meeting.duration else None,
                    "participant_count": len(meeting.participants),
                    "has_transcript": meeting.has_transcript(),
                    "summary": meeting.summary[:200] + "..." if meeting.summary and len(meeting.summary) > 200 else meeting.summary
                }
                results.append(result)

            return {
                "total_found": len(results),
                "meetings": results,
                "filters_applied": {
                    "query": query,
                    "from_date": from_date,
                    "to_date": to_date,
                    "participant": participant,
                    "limit": limit
                }
            }

        except Exception as e:
            raise MCPToolError(f"Search failed: {e}")

    def get_meeting(self, meeting_id: str) -> Dict[str, Any]:
        """
        Get complete meeting details.

        Args:
            meeting_id: Meeting ID to retrieve

        Returns:
            Dict containing complete meeting details
        """
        try:
            meetings = self._get_meetings()

            # Find the meeting
            meeting = None
            for m in meetings:
                if m.id == meeting_id:
                    meeting = m
                    break

            if not meeting:
                raise MCPToolError(f"Meeting not found: {meeting_id}")

            # Build complete meeting data
            result = {
                "id": meeting.id,
                "title": meeting.title,
                "start_time": meeting.start_time.isoformat() if meeting.start_time else None,
                "end_time": meeting.end_time.isoformat() if meeting.end_time else None,
                "duration_minutes": int(meeting.duration.total_seconds() / 60) if meeting.duration else None,
                "participants": meeting.participants,
                "summary": meeting.summary,
                "tags": meeting.tags,
                "has_transcript": meeting.has_transcript()
            }

            # Add transcript info if available
            if meeting.has_transcript() and meeting.transcript:
                transcript = meeting.transcript
                result["transcript_info"] = {
                    "word_count": transcript.word_count,
                    "speakers": transcript.speakers,
                    "segment_count": len(transcript.segments),
                    "duration_seconds": transcript.duration
                }

            return result

        except MCPToolError:
            raise
        except Exception as e:
            raise MCPToolError(f"Failed to get meeting: {e}")

    def get_transcript(self, meeting_id: str,
                      include_speakers: bool = True,
                      include_timestamps: bool = False) -> Dict[str, Any]:
        """
        Get full transcript for a meeting.

        Args:
            meeting_id: Meeting ID
            include_speakers: Include speaker identification
            include_timestamps: Include timestamps

        Returns:
            Dict containing transcript data
        """
        try:
            meetings = self._get_meetings()

            # Find the meeting
            meeting = None
            for m in meetings:
                if m.id == meeting_id:
                    meeting = m
                    break

            if not meeting:
                raise MCPToolError(f"Meeting not found: {meeting_id}")

            if not meeting.has_transcript():
                raise MCPToolError(f"Meeting has no transcript: {meeting_id}")

            transcript = meeting.transcript
            if not transcript:
                raise MCPToolError(f"Meeting transcript is None: {meeting_id}")

            # Build transcript response
            result = {
                "meeting_id": meeting_id,
                "meeting_title": meeting.title,
                "full_text": transcript.full_text,
                "word_count": transcript.word_count,
                "speakers": transcript.speakers,
                "segment_count": len(transcript.segments)
            }

            # Add segments with optional speaker/timestamp info
            segments = []
            for segment in transcript.segments:
                seg_data = {"text": segment.text}

                if include_speakers and segment.speaker:
                    seg_data["speaker"] = segment.speaker

                if include_timestamps:
                    if segment.timestamp:
                        seg_data["timestamp"] = segment.timestamp.isoformat()
                    if segment.start_time is not None:
                        seg_data["start_time"] = str(segment.start_time)
                    if segment.end_time is not None:
                        seg_data["end_time"] = str(segment.end_time)

                segments.append(seg_data)

            result["segments"] = segments

            return result

        except MCPToolError:
            raise
        except Exception as e:
            raise MCPToolError(f"Failed to get transcript: {e}")

    def get_meeting_notes(self, meeting_id: str) -> Dict[str, Any]:
        """
        Get structured notes and summary for a meeting.

        Args:
            meeting_id: Meeting ID

        Returns:
            Dict containing meeting notes and summary
        """
        try:
            meetings = self._get_meetings()

            # Find the meeting
            meeting = None
            for m in meetings:
                if m.id == meeting_id:
                    meeting = m
                    break

            if not meeting:
                raise MCPToolError(f"Meeting not found: {meeting_id}")

            result = {
                "meeting_id": meeting_id,
                "title": meeting.title,
                "date": meeting.start_time.strftime("%Y-%m-%d") if meeting.start_time else None,
                "duration": f"{int(meeting.duration.total_seconds() / 60)} minutes" if meeting.duration else None,
                "participants": meeting.participants,
                "summary": meeting.summary,
                "tags": meeting.tags
            }

            # Add transcript summary if available
            if meeting.has_transcript() and meeting.transcript:
                transcript = meeting.transcript

                # Basic transcript analysis
                speakers = transcript.speakers
                word_count = transcript.word_count

                result["transcript_summary"] = {
                    "total_words": word_count,
                    "speakers": speakers,
                    "speaker_count": len(speakers)
                }

                # Speaker participation analysis
                if len(transcript.segments) > 0:
                    speaker_words = defaultdict(int)
                    for segment in transcript.segments:
                        if segment.speaker and segment.text:
                            speaker_words[segment.speaker] += len(segment.text.split())

                    if speaker_words:
                        result["transcript_summary"]["speaker_participation"] = dict(speaker_words)

            return result

        except MCPToolError:
            raise
        except Exception as e:
            raise MCPToolError(f"Failed to get meeting notes: {e}")

    def list_participants(self, from_date: Optional[str] = None,
                         to_date: Optional[str] = None,
                         min_meetings: Optional[int] = None) -> Dict[str, Any]:
        """
        List all participants with frequency data.

        Args:
            from_date: Start date filter
            to_date: End date filter
            min_meetings: Minimum meeting count filter

        Returns:
            Dict containing participant list and statistics
        """
        try:
            meetings = self._get_meetings()

            # Apply date filters
            if from_date or to_date:
                meetings = self._filter_meetings_by_date(meetings, from_date, to_date)

            # Count participant occurrences
            participant_counts = Counter()
            participant_meetings = defaultdict(list)

            for meeting in meetings:
                for participant in meeting.participants:
                    participant_counts[participant] += 1
                    participant_meetings[participant].append({
                        "id": meeting.id,
                        "title": meeting.title,
                        "date": meeting.start_time.isoformat() if meeting.start_time else None
                    })

            # Apply minimum meetings filter
            if min_meetings:
                participant_counts = Counter({p: c for p, c in participant_counts.items() if c >= min_meetings})

            # Build results
            participants = []
            for participant, count in participant_counts.most_common():
                participants.append({
                    "name": participant,
                    "meeting_count": count,
                    "meetings": participant_meetings[participant]
                })

            return {
                "total_participants": len(participants),
                "total_meetings_analyzed": len(meetings),
                "participants": participants,
                "filters_applied": {
                    "from_date": from_date,
                    "to_date": to_date,
                    "min_meetings": min_meetings
                }
            }

        except Exception as e:
            raise MCPToolError(f"Failed to list participants: {e}")

    def get_statistics(self, stat_type: str,
                      from_date: Optional[str] = None,
                      to_date: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate meeting statistics and analytics.

        Args:
            stat_type: Type of statistics ("summary", "frequency", "duration", "participants", "patterns")
            from_date: Start date filter
            to_date: End date filter

        Returns:
            Dict containing statistical analysis
        """
        try:
            meetings = self._get_meetings()

            # Apply date filters
            if from_date or to_date:
                meetings = self._filter_meetings_by_date(meetings, from_date, to_date)

            if stat_type == "summary":
                return self._get_summary_statistics(meetings)
            elif stat_type == "frequency":
                return self._get_frequency_statistics(meetings)
            elif stat_type == "duration":
                return self._get_duration_statistics(meetings)
            elif stat_type == "participants":
                return self._get_participant_statistics(meetings)
            elif stat_type == "patterns":
                return self._get_pattern_statistics(meetings)
            else:
                raise MCPToolError(f"Unknown statistics type: {stat_type}")

        except MCPToolError:
            raise
        except Exception as e:
            raise MCPToolError(f"Failed to generate statistics: {e}")

    def _get_summary_statistics(self, meetings: List[Meeting]) -> Dict[str, Any]:
        """Generate summary statistics."""
        total_meetings = len(meetings)
        meetings_with_dates = len([m for m in meetings if m.start_time])
        meetings_with_durations = len([m for m in meetings if m.duration])
        meetings_with_transcripts = len([m for m in meetings if m.has_transcript()])

        # Date range
        dates = [m.start_time for m in meetings if m.start_time]
        date_range = None
        if dates:
            earliest = min(dates)
            latest = max(dates)
            date_range = {
                "earliest": earliest.isoformat(),
                "latest": latest.isoformat(),
                "span_days": (latest - earliest).days
            }

        # Duration statistics
        durations = [m.duration.total_seconds() / 60 for m in meetings if m.duration]
        duration_stats = None
        if durations:
            duration_stats = {
                "total_minutes": sum(durations),
                "average_minutes": statistics.mean(durations),
                "median_minutes": statistics.median(durations),
                "min_minutes": min(durations),
                "max_minutes": max(durations)
            }

        # Participant statistics
        all_participants = set()
        total_participations = 0
        for meeting in meetings:
            participants = meeting.participants
            all_participants.update(participants)
            total_participations += len(participants)

        return {
            "total_meetings": total_meetings,
            "date_coverage": f"{meetings_with_dates}/{total_meetings}" if total_meetings > 0 else "0/0",
            "duration_coverage": f"{meetings_with_durations}/{total_meetings}" if total_meetings > 0 else "0/0",
            "transcript_coverage": f"{meetings_with_transcripts}/{total_meetings}" if total_meetings > 0 else "0/0",
            "date_range": date_range,
            "duration_statistics": duration_stats,
            "participant_statistics": {
                "unique_participants": len(all_participants),
                "total_participations": total_participations,
                "average_participants_per_meeting": total_participations / total_meetings if total_meetings > 0 else 0
            }
        }

    def _get_frequency_statistics(self, meetings: List[Meeting]) -> Dict[str, Any]:
        """Generate frequency statistics."""
        # Daily frequency
        daily_counts = defaultdict(int)
        for meeting in meetings:
            if meeting.start_time:
                date_key = meeting.start_time.date().isoformat()
                daily_counts[date_key] += 1

        # Weekly frequency
        weekly_counts = defaultdict(int)
        for meeting in meetings:
            if meeting.start_time:
                monday = meeting.start_time.date() - datetime.timedelta(days=meeting.start_time.weekday())
                weekly_counts[monday.isoformat()] += 1

        # Monthly frequency
        monthly_counts = defaultdict(int)
        for meeting in meetings:
            if meeting.start_time:
                month_key = f"{meeting.start_time.year}-{meeting.start_time.month:02d}"
                monthly_counts[month_key] += 1

        return {
            "daily_frequency": dict(daily_counts),
            "weekly_frequency": dict(weekly_counts),
            "monthly_frequency": dict(monthly_counts),
            "peak_day": max(daily_counts.items(), key=lambda x: x[1]) if daily_counts else None,
            "peak_week": max(weekly_counts.items(), key=lambda x: x[1]) if weekly_counts else None,
            "peak_month": max(monthly_counts.items(), key=lambda x: x[1]) if monthly_counts else None
        }

    def _get_duration_statistics(self, meetings: List[Meeting]) -> Dict[str, Any]:
        """Generate duration statistics."""
        durations = [m.duration.total_seconds() / 60 for m in meetings if m.duration]

        if not durations:
            return {"error": "No duration data available"}

        # Duration distribution
        duration_ranges = {
            "0-15 min": 0,
            "15-30 min": 0,
            "30-60 min": 0,
            "60-90 min": 0,
            "90+ min": 0
        }

        for duration in durations:
            if duration <= 15:
                duration_ranges["0-15 min"] += 1
            elif duration <= 30:
                duration_ranges["15-30 min"] += 1
            elif duration <= 60:
                duration_ranges["30-60 min"] += 1
            elif duration <= 90:
                duration_ranges["60-90 min"] += 1
            else:
                duration_ranges["90+ min"] += 1

        return {
            "total_meetings": len(durations),
            "total_minutes": sum(durations),
            "average_minutes": statistics.mean(durations),
            "median_minutes": statistics.median(durations),
            "min_minutes": min(durations),
            "max_minutes": max(durations),
            "std_dev_minutes": statistics.stdev(durations) if len(durations) > 1 else 0,
            "duration_distribution": duration_ranges
        }

    def _get_participant_statistics(self, meetings: List[Meeting]) -> Dict[str, Any]:
        """Generate participant statistics."""
        participant_counts = Counter()
        meeting_sizes = []

        for meeting in meetings:
            participants = meeting.participants
            meeting_sizes.append(len(participants))
            for participant in participants:
                participant_counts[participant] += 1

        if not participant_counts:
            return {"error": "No participant data available"}

        return {
            "unique_participants": len(participant_counts),
            "total_participations": sum(participant_counts.values()),
            "average_meeting_size": statistics.mean(meeting_sizes) if meeting_sizes else 0,
            "median_meeting_size": statistics.median(meeting_sizes) if meeting_sizes else 0,
            "max_meeting_size": max(meeting_sizes) if meeting_sizes else 0,
            "min_meeting_size": min(meeting_sizes) if meeting_sizes else 0,
            "top_participants": participant_counts.most_common(10),
            "meeting_size_distribution": dict(Counter(meeting_sizes))
        }

    def _get_pattern_statistics(self, meetings: List[Meeting]) -> Dict[str, Any]:
        """Generate time pattern statistics."""
        hourly_counts = defaultdict(int)
        daily_counts = defaultdict(int)  # 0=Monday, 6=Sunday

        for meeting in meetings:
            if meeting.start_time:
                hour = meeting.start_time.hour
                day_of_week = meeting.start_time.weekday()
                hourly_counts[hour] += 1
                daily_counts[day_of_week] += 1

        # Convert to readable format
        day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        daily_patterns = {day_names[day]: count for day, count in daily_counts.items()}

        return {
            "hourly_patterns": dict(hourly_counts),
            "daily_patterns": daily_patterns,
            "peak_hour": max(hourly_counts.items(), key=lambda x: x[1]) if hourly_counts else None,
            "peak_day": day_names[max(daily_counts.items(), key=lambda x: x[1])[0]] if daily_counts else None
        }

    def export_meeting(self, meeting_id: str,
                      include_transcript: bool = True,
                      include_metadata: bool = True) -> Dict[str, Any]:
        """
        Export meeting in markdown format.

        Args:
            meeting_id: Meeting ID to export
            include_transcript: Include full transcript
            include_metadata: Include meeting metadata

        Returns:
            Dict containing markdown content
        """
        try:
            meetings = self._get_meetings()

            # Find the meeting
            meeting = None
            for m in meetings:
                if m.id == meeting_id:
                    meeting = m
                    break

            if not meeting:
                raise MCPToolError(f"Meeting not found: {meeting_id}")

            # Use the existing markdown export function
            markdown_content = export_meeting_to_markdown(
                meeting,
                include_transcript=include_transcript,
                include_metadata=include_metadata
            )

            return {
                "meeting_id": meeting_id,
                "title": meeting.title,
                "format": "markdown",
                "content": markdown_content,
                "includes_transcript": include_transcript and meeting.has_transcript(),
                "includes_metadata": include_metadata
            }

        except MCPToolError:
            raise
        except Exception as e:
            raise MCPToolError(f"Failed to export meeting: {e}")

    def analyze_patterns(self, pattern_type: str,
                        from_date: Optional[str] = None,
                        to_date: Optional[str] = None) -> Dict[str, Any]:
        """
        Analyze meeting patterns and trends.

        Args:
            pattern_type: Type of pattern analysis ("time", "frequency", "participants", "duration")
            from_date: Start date filter
            to_date: End date filter

        Returns:
            Dict containing pattern analysis
        """
        try:
            meetings = self._get_meetings()

            # Apply date filters
            if from_date or to_date:
                meetings = self._filter_meetings_by_date(meetings, from_date, to_date)

            if pattern_type == "time":
                return self._analyze_time_patterns(meetings)
            elif pattern_type == "frequency":
                return self._analyze_frequency_patterns(meetings)
            elif pattern_type == "participants":
                return self._analyze_participant_patterns(meetings)
            elif pattern_type == "duration":
                return self._analyze_duration_patterns(meetings)
            else:
                raise MCPToolError(f"Unknown pattern type: {pattern_type}")

        except MCPToolError:
            raise
        except Exception as e:
            raise MCPToolError(f"Failed to analyze patterns: {e}")

    def _analyze_time_patterns(self, meetings: List[Meeting]) -> Dict[str, Any]:
        """Analyze time-based patterns."""
        return self._get_pattern_statistics(meetings)

    def _analyze_frequency_patterns(self, meetings: List[Meeting]) -> Dict[str, Any]:
        """Analyze frequency patterns."""
        return self._get_frequency_statistics(meetings)

    def _analyze_participant_patterns(self, meetings: List[Meeting]) -> Dict[str, Any]:
        """Analyze participant patterns."""
        # Find frequent collaborations
        participant_pairs = Counter()

        for meeting in meetings:
            participants = meeting.participants
            if len(participants) >= 2:
                # Count all pairs of participants
                for i, p1 in enumerate(participants):
                    for p2 in participants[i+1:]:
                        pair = tuple(sorted([p1, p2]))
                        participant_pairs[pair] += 1

        # Get participant statistics
        participant_stats = self._get_participant_statistics(meetings)

        return {
            **participant_stats,
            "frequent_collaborations": participant_pairs.most_common(10),
            "collaboration_analysis": {
                "total_unique_pairs": len(participant_pairs),
                "most_frequent_pair": participant_pairs.most_common(1)[0] if participant_pairs else None
            }
        }

    def _analyze_duration_patterns(self, meetings: List[Meeting]) -> Dict[str, Any]:
        """Analyze duration patterns."""
        duration_stats = self._get_duration_statistics(meetings)

        # Add trend analysis if we have enough data
        if len(meetings) > 5:
            # Sort meetings by date
            dated_meetings = [m for m in meetings if m.start_time and m.duration]
            dated_meetings.sort(key=lambda m: m.start_time or datetime.datetime.min)

            if len(dated_meetings) > 2:
                # Simple trend analysis
                durations = [m.duration.total_seconds() / 60 for m in dated_meetings if m.duration]
                first_half = durations[:len(durations)//2]
                second_half = durations[len(durations)//2:]

                trend = "stable"
                if len(first_half) > 0 and len(second_half) > 0:
                    first_avg = statistics.mean(first_half)
                    second_avg = statistics.mean(second_half)

                    if second_avg > first_avg * 1.1:
                        trend = "increasing"
                    elif second_avg < first_avg * 0.9:
                        trend = "decreasing"

                duration_stats["trend_analysis"] = {
                    "trend": trend,
                    "first_half_avg": statistics.mean(first_half) if first_half else 0,
                    "second_half_avg": statistics.mean(second_half) if second_half else 0
                }

        return duration_stats

    def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a specific MCP tool with given arguments.

        Args:
            tool_name: Name of the tool to execute
            arguments: Tool arguments

        Returns:
            Dict containing tool execution results
        """
        if tool_name == "search_meetings":
            return self.search_meetings(**arguments)
        elif tool_name == "get_meeting":
            return self.get_meeting(**arguments)
        elif tool_name == "get_transcript":
            return self.get_transcript(**arguments)
        elif tool_name == "get_meeting_notes":
            return self.get_meeting_notes(**arguments)
        elif tool_name == "list_participants":
            return self.list_participants(**arguments)
        elif tool_name == "get_statistics":
            return self.get_statistics(**arguments)
        elif tool_name == "export_meeting":
            return self.export_meeting(**arguments)
        elif tool_name == "analyze_patterns":
            return self.analyze_patterns(**arguments)
        else:
            raise MCPToolError(f"Unknown tool: {tool_name}")

    def get_tool_schemas(self) -> List[Dict[str, Any]]:
        """
        Get MCP tool schemas for all available tools.

        Returns:
            List of tool schema definitions
        """
        return [
            {
                "name": "search_meetings",
                "description": "Search meetings with flexible filters including text search, date range, and participant filters",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Text search in title/content (optional)"
                        },
                        "from_date": {
                            "type": "string",
                            "description": "Start date (ISO format or relative like '30d') (optional)"
                        },
                        "to_date": {
                            "type": "string",
                            "description": "End date (ISO format or relative like '1d') (optional)"
                        },
                        "participant": {
                            "type": "string",
                            "description": "Filter by participant email/name (optional)"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of results (optional)"
                        }
                    }
                }
            },
            {
                "name": "get_meeting",
                "description": "Get complete meeting details including metadata, participants, and transcript info",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "meeting_id": {
                            "type": "string",
                            "description": "Meeting ID to retrieve"
                        }
                    },
                    "required": ["meeting_id"]
                }
            },
            {
                "name": "get_transcript",
                "description": "Get full transcript for a specific meeting with optional speaker and timestamp information",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "meeting_id": {
                            "type": "string",
                            "description": "Meeting ID to retrieve transcript for"
                        },
                        "include_speakers": {
                            "type": "boolean",
                            "description": "Include speaker identification (default: true)"
                        },
                        "include_timestamps": {
                            "type": "boolean",
                            "description": "Include timestamps (default: false)"
                        }
                    },
                    "required": ["meeting_id"]
                }
            },
            {
                "name": "get_meeting_notes",
                "description": "Get structured notes and summary for a meeting",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "meeting_id": {
                            "type": "string",
                            "description": "Meeting ID to get notes for"
                        }
                    },
                    "required": ["meeting_id"]
                }
            },
            {
                "name": "list_participants",
                "description": "List all participants with frequency data and meeting history",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "from_date": {
                            "type": "string",
                            "description": "Start date filter (optional)"
                        },
                        "to_date": {
                            "type": "string",
                            "description": "End date filter (optional)"
                        },
                        "min_meetings": {
                            "type": "integer",
                            "description": "Minimum meeting count filter (optional)"
                        }
                    }
                }
            },
            {
                "name": "get_statistics",
                "description": "Generate meeting statistics and analytics",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "stat_type": {
                            "type": "string",
                            "description": "Type of statistics: summary, frequency, duration, participants, patterns",
                            "enum": ["summary", "frequency", "duration", "participants", "patterns"]
                        },
                        "from_date": {
                            "type": "string",
                            "description": "Start date filter (optional)"
                        },
                        "to_date": {
                            "type": "string",
                            "description": "End date filter (optional)"
                        }
                    },
                    "required": ["stat_type"]
                }
            },
            {
                "name": "export_meeting",
                "description": "Export meeting in markdown format",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "meeting_id": {
                            "type": "string",
                            "description": "Meeting ID to export"
                        },
                        "include_transcript": {
                            "type": "boolean",
                            "description": "Include full transcript (default: true)"
                        },
                        "include_metadata": {
                            "type": "boolean",
                            "description": "Include meeting metadata (default: true)"
                        }
                    },
                    "required": ["meeting_id"]
                }
            },
            {
                "name": "analyze_patterns",
                "description": "Analyze meeting patterns and trends",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "pattern_type": {
                            "type": "string",
                            "description": "Type of pattern analysis: time, frequency, participants, duration",
                            "enum": ["time", "frequency", "participants", "duration"]
                        },
                        "from_date": {
                            "type": "string",
                            "description": "Start date filter (optional)"
                        },
                        "to_date": {
                            "type": "string",
                            "description": "End date filter (optional)"
                        }
                    },
                    "required": ["pattern_type"]
                }
            }
        ]