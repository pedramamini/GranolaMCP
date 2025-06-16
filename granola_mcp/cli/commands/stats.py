"""
Statistics command implementation for GranolaMCP CLI.

Provides comprehensive statistics and analytics for meeting data including
frequency analysis, duration distribution, participant tracking, and time patterns.
"""

import argparse
import datetime
import statistics
from collections import defaultdict, Counter
from typing import List, Dict, Any, Optional, Tuple
from ...core.parser import GranolaParser
from ...core.meeting import Meeting
from ...utils.date_parser import parse_date, get_date_range
from ..formatters.colors import (
    Colors, colorize, format_duration, format_participant_count,
    print_error, print_info, print_header, print_subheader, muted, header, subheader
)
from ..formatters.charts import (
    create_bar_chart, create_histogram, create_line_chart,
    create_time_pattern_chart, create_day_pattern_chart, create_summary_box
)


class StatsCommand:
    """Command to generate meeting statistics and visualizations."""

    def __init__(self, parser: GranolaParser, args: argparse.Namespace):
        """
        Initialize the stats command.

        Args:
            parser: GranolaParser instance
            args: Parsed command line arguments
        """
        self.parser = parser
        self.args = args

    @staticmethod
    def add_arguments(parser: argparse.ArgumentParser) -> None:
        """
        Add arguments for the stats command.

        Args:
            parser: Argument parser to add arguments to
        """
        # Date filtering options
        date_group = parser.add_mutually_exclusive_group()
        date_group.add_argument(
            '--last',
            type=str,
            help='Analyze meetings from the last period (e.g., 30d, 12w, 6m)'
        )

        date_group.add_argument(
            '--from',
            dest='from_date',
            type=str,
            help='Start date for analysis (YYYY-MM-DD or relative like 30d)'
        )

        parser.add_argument(
            '--to',
            dest='to_date',
            type=str,
            help='End date for analysis (YYYY-MM-DD or relative like 1d). Only used with --from'
        )

        # Analysis type options
        analysis_group = parser.add_mutually_exclusive_group()
        analysis_group.add_argument(
            '--meetings-per-day',
            action='store_true',
            help='Show meetings per day analysis'
        )

        analysis_group.add_argument(
            '--meetings-per-week',
            action='store_true',
            help='Show meetings per week analysis'
        )

        analysis_group.add_argument(
            '--meetings-per-month',
            action='store_true',
            help='Show meetings per month analysis'
        )

        analysis_group.add_argument(
            '--duration-distribution',
            action='store_true',
            help='Show meeting duration distribution'
        )

        analysis_group.add_argument(
            '--participant-frequency',
            action='store_true',
            help='Show participant frequency analysis'
        )

        analysis_group.add_argument(
            '--time-patterns',
            action='store_true',
            help='Show meeting time patterns (hour/day of week)'
        )

        analysis_group.add_argument(
            '--word-analysis',
            action='store_true',
            help='Show transcript word count analysis'
        )

        analysis_group.add_argument(
            '--summary',
            action='store_true',
            help='Show comprehensive statistics summary'
        )

        analysis_group.add_argument(
            '--all',
            action='store_true',
            help='Show all available statistics'
        )

        # Filtering options
        parser.add_argument(
            '--folder',
            type=str,
            help='Filter meetings by folder name'
        )

        # Output options
        parser.add_argument(
            '--no-charts',
            action='store_true',
            help='Disable ASCII charts (text only)'
        )

        parser.add_argument(
            '--chart-width',
            type=int,
            help='Width for ASCII charts'
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
                end_date = datetime.datetime.now(start_date.tzinfo)
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

    def _filter_meetings_by_folder(self, meetings: List[Meeting]) -> List[Meeting]:
        """
        Filter meetings by folder name.

        Args:
            meetings: List of meetings to filter

        Returns:
            List[Meeting]: Filtered meetings
        """
        if not self.args.folder:
            return meetings

        folder_name = self.args.folder.lower()
        filtered_meetings = []
        
        for meeting in meetings:
            meeting_folder = meeting.folder_name
            if meeting_folder and meeting_folder.lower() == folder_name:
                filtered_meetings.append(meeting)

        return filtered_meetings

    def _analyze_meetings_per_day(self, meetings: List[Meeting]) -> None:
        """Analyze and display meetings per day."""
        if not meetings:
            print_info("No meetings found for analysis.")
            return

        print_header("📅 Meetings Per Day Analysis")
        print()

        # Group meetings by date
        daily_counts = defaultdict(int)
        for meeting in meetings:
            if meeting.start_time:
                date_key = meeting.start_time.date()
                daily_counts[date_key] += 1

        if not daily_counts:
            print_info("No meetings with valid dates found.")
            return

        # Sort by date
        sorted_dates = sorted(daily_counts.keys())

        # Calculate statistics
        counts = list(daily_counts.values())
        avg_per_day = statistics.mean(counts)
        max_per_day = max(counts)
        total_days = len(daily_counts)
        total_meetings = sum(counts)

        # Display summary
        summary_stats = {
            "Total Days": total_days,
            "Total Meetings": total_meetings,
            "Average per Day": f"{avg_per_day:.1f}",
            "Max per Day": max_per_day,
            "Days with Meetings": len([c for c in counts if c > 0])
        }

        print(create_summary_box(summary_stats, "Daily Meeting Summary"))
        print()

        # Create chart if enabled
        if not self.args.no_charts:
            # Show last 30 days or all data if less
            chart_data = []
            display_dates = sorted_dates[-30:] if len(sorted_dates) > 30 else sorted_dates

            for date in display_dates:
                count = daily_counts[date]
                date_str = date.strftime("%m/%d")
                chart_data.append((date_str, count))

            chart_title = f"Meetings Per Day ({len(chart_data)} days)"
            print(create_bar_chart(
                chart_data,
                chart_title,
                width=self.args.chart_width,
                color=Colors.BLUE
            ))

    def _analyze_meetings_per_week(self, meetings: List[Meeting]) -> None:
        """Analyze and display meetings per week."""
        if not meetings:
            print_info("No meetings found for analysis.")
            return

        print_header("📊 Meetings Per Week Analysis")
        print()

        # Group meetings by week
        weekly_counts = defaultdict(int)
        for meeting in meetings:
            if meeting.start_time:
                # Get Monday of the week
                monday = meeting.start_time.date() - datetime.timedelta(days=meeting.start_time.weekday())
                weekly_counts[monday] += 1

        if not weekly_counts:
            print_info("No meetings with valid dates found.")
            return

        # Sort by week
        sorted_weeks = sorted(weekly_counts.keys())

        # Calculate statistics
        counts = list(weekly_counts.values())
        avg_per_week = statistics.mean(counts)
        max_per_week = max(counts)
        total_weeks = len(weekly_counts)
        total_meetings = sum(counts)

        # Display summary
        summary_stats = {
            "Total Weeks": total_weeks,
            "Total Meetings": total_meetings,
            "Average per Week": f"{avg_per_week:.1f}",
            "Max per Week": max_per_week,
            "Weeks with Meetings": len([c for c in counts if c > 0])
        }

        print(create_summary_box(summary_stats, "Weekly Meeting Summary"))
        print()

        # Create chart if enabled
        if not self.args.no_charts:
            chart_data = []
            for week_start in sorted_weeks:
                count = weekly_counts[week_start]
                week_str = week_start.strftime("%m/%d")
                chart_data.append((week_str, count))

            chart_title = f"Meetings Per Week ({len(chart_data)} weeks)"
            print(create_bar_chart(
                chart_data,
                chart_title,
                width=self.args.chart_width,
                color=Colors.GREEN
            ))

    def _analyze_meetings_per_month(self, meetings: List[Meeting]) -> None:
        """Analyze and display meetings per month."""
        if not meetings:
            print_info("No meetings found for analysis.")
            return

        print_header("📈 Meetings Per Month Analysis")
        print()

        # Group meetings by month
        monthly_counts = defaultdict(int)
        for meeting in meetings:
            if meeting.start_time:
                month_key = (meeting.start_time.year, meeting.start_time.month)
                monthly_counts[month_key] += 1

        if not monthly_counts:
            print_info("No meetings with valid dates found.")
            return

        # Sort by month
        sorted_months = sorted(monthly_counts.keys())

        # Calculate statistics
        counts = list(monthly_counts.values())
        avg_per_month = statistics.mean(counts)
        max_per_month = max(counts)
        total_months = len(monthly_counts)
        total_meetings = sum(counts)

        # Display summary
        summary_stats = {
            "Total Months": total_months,
            "Total Meetings": total_meetings,
            "Average per Month": f"{avg_per_month:.1f}",
            "Max per Month": max_per_month,
            "Months with Meetings": len([c for c in counts if c > 0])
        }

        print(create_summary_box(summary_stats, "Monthly Meeting Summary"))
        print()

        # Create chart if enabled
        if not self.args.no_charts:
            chart_data = []
            for year, month in sorted_months:
                count = monthly_counts[(year, month)]
                month_str = f"{year}-{month:02d}"
                chart_data.append((month_str, count))

            chart_title = f"Meetings Per Month ({len(chart_data)} months)"
            print(create_bar_chart(
                chart_data,
                chart_title,
                width=self.args.chart_width,
                color=Colors.CYAN
            ))

    def _analyze_duration_distribution(self, meetings: List[Meeting]) -> None:
        """Analyze and display meeting duration distribution."""
        print_header("⏱️  Meeting Duration Distribution")
        print()

        # Extract durations in minutes
        durations = []
        for meeting in meetings:
            if meeting.duration:
                duration_minutes = meeting.duration.total_seconds() / 60
                durations.append(duration_minutes)

        if not durations:
            print_info("No meetings with duration data found.")
            return

        # Calculate statistics
        avg_duration = statistics.mean(durations)
        median_duration = statistics.median(durations)
        min_duration = min(durations)
        max_duration = max(durations)

        try:
            stdev_duration = statistics.stdev(durations) if len(durations) > 1 else 0
        except statistics.StatisticsError:
            stdev_duration = 0

        # Display summary
        summary_stats = {
            "Total Meetings": len(durations),
            "Average Duration": format_duration(avg_duration * 60),
            "Median Duration": format_duration(median_duration * 60),
            "Min Duration": format_duration(min_duration * 60),
            "Max Duration": format_duration(max_duration * 60),
            "Std Deviation": f"{stdev_duration:.1f}m"
        }

        print(create_summary_box(summary_stats, "Duration Statistics"))
        print()

        # Create histogram if enabled
        if not self.args.no_charts:
            print(create_histogram(
                durations,
                bins=10,
                title="Duration Distribution (minutes)",
                width=self.args.chart_width
            ))

    def _analyze_participant_frequency(self, meetings: List[Meeting]) -> None:
        """Analyze and display participant frequency."""
        print_header("👥 Participant Frequency Analysis")
        print()

        # Count participant occurrences
        participant_counts = Counter()
        meeting_sizes = []

        for meeting in meetings:
            participants = meeting.participants
            meeting_sizes.append(len(participants))
            for participant in participants:
                participant_counts[participant] += 1

        if not participant_counts:
            print_info("No participant data found.")
            return

        # Calculate statistics
        total_participants = len(participant_counts)
        total_participations = sum(participant_counts.values())
        avg_meeting_size = statistics.mean(meeting_sizes) if meeting_sizes else 0

        # Display summary
        summary_stats = {
            "Unique Participants": total_participants,
            "Total Participations": total_participations,
            "Average Meeting Size": f"{avg_meeting_size:.1f}",
            "Max Meeting Size": max(meeting_sizes) if meeting_sizes else 0,
            "Min Meeting Size": min(meeting_sizes) if meeting_sizes else 0
        }

        print(create_summary_box(summary_stats, "Participant Statistics"))
        print()

        # Show top participants
        if not self.args.no_charts:
            top_participants = participant_counts.most_common(15)
            chart_data = []

            for participant, count in top_participants:
                # Truncate long names
                display_name = participant[:20] + "..." if len(participant) > 23 else participant
                chart_data.append((display_name, count))

            if chart_data:
                print(create_bar_chart(
                    chart_data,
                    "Top Participants by Meeting Count",
                    width=self.args.chart_width,
                    color=Colors.MAGENTA
                ))

    def _analyze_time_patterns(self, meetings: List[Meeting]) -> None:
        """Analyze and display meeting time patterns."""
        print_header("🕐 Meeting Time Patterns")
        print()

        # Analyze by hour of day
        hourly_counts = defaultdict(int)
        daily_counts = defaultdict(int)  # 0=Monday, 6=Sunday

        for meeting in meetings:
            if meeting.start_time:
                hour = meeting.start_time.hour
                day_of_week = meeting.start_time.weekday()
                hourly_counts[hour] += 1
                daily_counts[day_of_week] += 1

        if not hourly_counts and not daily_counts:
            print_info("No meetings with time data found.")
            return

        # Display charts if enabled
        if not self.args.no_charts:
            if hourly_counts:
                print(create_time_pattern_chart(hourly_counts))
                print()

            if daily_counts:
                print(create_day_pattern_chart(daily_counts))

        # Display peak times
        if hourly_counts:
            peak_hour = max(hourly_counts.items(), key=lambda x: x[1])
            peak_hour_str = f"{peak_hour[0]:02d}:00"
            print_info(f"Peak meeting hour: {peak_hour_str} ({peak_hour[1]} meetings)")

        if daily_counts:
            days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            peak_day = max(daily_counts.items(), key=lambda x: x[1])
            peak_day_str = days[peak_day[0]]
            print_info(f"Peak meeting day: {peak_day_str} ({peak_day[1]} meetings)")

    def _analyze_word_analysis(self, meetings: List[Meeting]) -> None:
        """Analyze transcript word counts and content."""
        print_header("📝 Transcript Word Analysis")
        print()

        transcript_lengths = []
        meetings_with_transcripts = 0
        total_words = 0

        for meeting in meetings:
            if meeting.has_transcript() and meeting.transcript:
                meetings_with_transcripts += 1
                # Simple word count (split by whitespace)
                transcript_text = meeting.transcript.full_text
                if transcript_text:
                    word_count = len(transcript_text.split())
                    transcript_lengths.append(word_count)
                    total_words += word_count

        if not transcript_lengths:
            print_info("No meetings with transcript data found.")
            return

        # Calculate statistics
        avg_words = statistics.mean(transcript_lengths)
        median_words = statistics.median(transcript_lengths)
        min_words = min(transcript_lengths)
        max_words = max(transcript_lengths)

        # Display summary
        summary_stats = {
            "Meetings with Transcripts": meetings_with_transcripts,
            "Total Meetings": len(meetings),
            "Coverage": f"{(meetings_with_transcripts/len(meetings)*100):.1f}%",
            "Total Words": f"{total_words:,}",
            "Average Words/Meeting": f"{avg_words:.0f}",
            "Median Words/Meeting": f"{median_words:.0f}"
        }

        print(create_summary_box(summary_stats, "Transcript Statistics"))
        print()

        # Create histogram if enabled
        if not self.args.no_charts and len(transcript_lengths) > 1:
            print(create_histogram(
                transcript_lengths,
                bins=8,
                title="Transcript Length Distribution (words)",
                width=self.args.chart_width
            ))

    def _show_comprehensive_summary(self, meetings: List[Meeting]) -> None:
        """Show a comprehensive statistics summary."""
        print_header("📊 Comprehensive Meeting Statistics")
        print()

        if not meetings:
            print_info("No meetings found for analysis.")
            return

        # Basic counts
        total_meetings = len(meetings)
        meetings_with_dates = len([m for m in meetings if m.start_time])
        meetings_with_durations = len([m for m in meetings if m.duration])
        meetings_with_transcripts = len([m for m in meetings if m.has_transcript()])

        # Date range
        dates = [m.start_time for m in meetings if m.start_time]
        date_range = ""
        if dates:
            earliest = min(dates)
            latest = max(dates)
            date_range = f"{earliest.strftime('%Y-%m-%d')} to {latest.strftime('%Y-%m-%d')}"

        # Duration statistics
        durations = [m.duration.total_seconds() / 60 for m in meetings if m.duration]
        avg_duration = statistics.mean(durations) if durations else 0
        total_duration = sum(durations) if durations else 0

        # Participant statistics
        all_participants = set()
        total_participations = 0
        for meeting in meetings:
            participants = meeting.participants
            all_participants.update(participants)
            total_participations += len(participants)

        # Display comprehensive summary
        summary_stats = {
            "Total Meetings": total_meetings,
            "Date Range": date_range or "Unknown",
            "Meetings with Dates": f"{meetings_with_dates} ({meetings_with_dates/total_meetings*100:.1f}%)",
            "Meetings with Durations": f"{meetings_with_durations} ({meetings_with_durations/total_meetings*100:.1f}%)",
            "Meetings with Transcripts": f"{meetings_with_transcripts} ({meetings_with_transcripts/total_meetings*100:.1f}%)",
            "Total Duration": format_duration(total_duration * 60),
            "Average Duration": format_duration(avg_duration * 60),
            "Unique Participants": len(all_participants),
            "Total Participations": total_participations,
            "Avg Participants/Meeting": f"{total_participations/total_meetings:.1f}" if total_meetings > 0 else "0"
        }

        print(create_summary_box(summary_stats, "Overall Statistics"))

    def execute(self) -> int:
        """
        Execute the stats command.

        Returns:
            int: Exit code (0 for success)
        """
        try:
            # Load meetings
            meeting_data = self.parser.get_meetings()
            meetings = [Meeting(data) for data in meeting_data]

            if self.args.verbose:
                print_info(f"Loaded {len(meetings)} meetings from cache")

            # Apply date filters
            meetings = self._filter_meetings_by_date(meetings)

            if self.args.verbose and len(meetings) != len(meeting_data):
                print_info(f"Filtered to {len(meetings)} meetings based on date criteria")

            # Apply folder filters
            original_count = len(meetings)
            meetings = self._filter_meetings_by_folder(meetings)

            if self.args.verbose and len(meetings) != original_count and self.args.folder:
                print_info(f"Filtered to {len(meetings)} meetings in folder '{self.args.folder}'")

            # Execute the appropriate analysis
            if self.args.meetings_per_day:
                self._analyze_meetings_per_day(meetings)
            elif self.args.meetings_per_week:
                self._analyze_meetings_per_week(meetings)
            elif self.args.meetings_per_month:
                self._analyze_meetings_per_month(meetings)
            elif self.args.duration_distribution:
                self._analyze_duration_distribution(meetings)
            elif self.args.participant_frequency:
                self._analyze_participant_frequency(meetings)
            elif self.args.time_patterns:
                self._analyze_time_patterns(meetings)
            elif self.args.word_analysis:
                self._analyze_word_analysis(meetings)
            elif self.args.summary:
                self._show_comprehensive_summary(meetings)
            elif self.args.all:
                # Show all analyses
                self._show_comprehensive_summary(meetings)
                print("\n" + "="*60 + "\n")
                self._analyze_meetings_per_day(meetings)
                print("\n" + "="*60 + "\n")
                self._analyze_duration_distribution(meetings)
                print("\n" + "="*60 + "\n")
                self._analyze_participant_frequency(meetings)
                print("\n" + "="*60 + "\n")
                self._analyze_time_patterns(meetings)
                if any(m.has_transcript() for m in meetings):
                    print("\n" + "="*60 + "\n")
                    self._analyze_word_analysis(meetings)
            else:
                # Default to summary
                self._show_comprehensive_summary(meetings)

            return 0

        except Exception as e:
            print_error(f"Error generating statistics: {e}")
            if self.args.verbose:
                import traceback
                traceback.print_exc()
            return 1