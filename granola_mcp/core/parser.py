"""
JSON parser for GranolaMCP.

Provides the GranolaParser class for loading and parsing Granola.ai cache files
with double JSON parsing and proper error handling.
"""

import json
import os
from typing import Dict, Any, List, Optional
from ..utils.config import get_cache_path, validate_cache_path


class GranolaParseError(Exception):
    """Custom exception for Granola parsing errors."""
    pass


class GranolaParser:
    """
    Parser for Granola.ai cache files.

    Handles the double JSON parsing required for Granola cache files:
    1. Parse the outer JSON structure
    2. Parse the inner 'cache' field which contains JSON as a string
    """

    def __init__(self, cache_path: Optional[str] = None):
        """
        Initialize the GranolaParser.

        Args:
            cache_path: Path to the cache file (if None, uses config default)
        """
        self.cache_path = cache_path or get_cache_path()
        self._cache_data: Optional[Dict[str, Any]] = None
        self._raw_data: Optional[str] = None

    def load_cache(self, force_reload: bool = False) -> Dict[str, Any]:
        """
        Load and parse the Granola cache file.

        Args:
            force_reload: If True, reload even if already cached

        Returns:
            Dict[str, Any]: Parsed cache data

        Raises:
            GranolaParseError: If cache file cannot be loaded or parsed
        """
        if self._cache_data is not None and not force_reload:
            return self._cache_data

        # Validate cache file exists and is readable
        if not validate_cache_path(self.cache_path):
            raise GranolaParseError(f"Cache file not found or not readable: {self.cache_path}")

        try:
            # Read the raw file content
            with open(self.cache_path, 'r', encoding='utf-8') as f:
                self._raw_data = f.read()

            # First JSON parse - get the outer structure
            try:
                outer_data = json.loads(self._raw_data)
            except json.JSONDecodeError as e:
                raise GranolaParseError(f"Invalid JSON in cache file: {e}") from e

            # Validate outer structure has 'cache' field
            if not isinstance(outer_data, dict):
                raise GranolaParseError("Cache file must contain a JSON object")

            if 'cache' not in outer_data:
                raise GranolaParseError("Cache file missing required 'cache' field")

            cache_content = outer_data['cache']
            if not isinstance(cache_content, str):
                raise GranolaParseError("Cache field must contain a JSON string")

            # Second JSON parse - parse the inner cache content
            try:
                self._cache_data = json.loads(cache_content)
            except json.JSONDecodeError as e:
                raise GranolaParseError(f"Invalid JSON in cache content: {e}") from e

            if not isinstance(self._cache_data, dict):
                raise GranolaParseError("Cache content must be a JSON object")

            return self._cache_data

        except Exception as e:
            if isinstance(e, GranolaParseError):
                raise
            raise GranolaParseError(f"Error loading cache file: {e}") from e

    def get_meetings(self, debug: bool = False) -> List[Dict[str, Any]]:
        """
        Get all meetings from the cache.

        Args:
            debug: If True, print debug information about cache structure

        Returns:
            List[Dict[str, Any]]: List of meeting objects

        Raises:
            GranolaParseError: If cache cannot be loaded or meetings not found
        """
        cache_data = self.load_cache()

        if debug:
            print(f"DEBUG: Cache data keys: {list(cache_data.keys())}")

        # Look for meetings in common locations
        meetings = None
        found_location = None

        # Expanded list of possible meeting field names
        meeting_field_names = [
            'events', 'meetings', 'sessions', 'data', 'items', 'calls', 'recordings',
            'transcripts', 'conversations', 'entries', 'history', 'records', 'list',
            'content', 'cache_data', 'meeting_data', 'session_data', 'event_data'
        ]

        # First check if there's a 'state' key (Granola v3 format)
        if 'state' in cache_data and isinstance(cache_data['state'], dict):
            state_data = cache_data['state']
            if debug:
                print(f"DEBUG: Found 'state' key with keys: {list(state_data.keys())}")

            # Try different possible keys for meetings within state
            for key in meeting_field_names:
                if key in state_data:
                    meetings = state_data[key]
                    found_location = f"state.{key}"
                    if debug:
                        print(f"DEBUG: Found meetings at {found_location}, type: {type(meetings)}, length: {len(meetings) if isinstance(meetings, list) else 'N/A'}")
                    break

            # If no standard key found in state, look for any list in state
            if meetings is None:
                if debug:
                    print("DEBUG: No standard keys found in state, looking for any lists...")
                for key, value in state_data.items():
                    if isinstance(value, list) and len(value) > 0:
                        # Check if this list contains meeting-like objects
                        first_item = value[0]
                        if isinstance(first_item, dict):
                            # Look for meeting-like fields in the first item
                            meeting_indicators = [
                                'id', 'meeting_id', 'session_id', 'uuid', 'title', 'name', 'subject',
                                'start_time', 'startTime', 'created_at', 'timestamp', 'date',
                                'participants', 'attendees', 'transcript', 'transcription'
                            ]
                            found_indicators = [field for field in meeting_indicators if field in first_item]
                            if found_indicators:
                                meetings = value
                                found_location = f"state.{key}"
                                if debug:
                                    print(f"DEBUG: Found potential meetings at {found_location} with indicators: {found_indicators}")
                                break

        # Fallback: Try different possible keys for meetings at root level
        if meetings is None:
            if debug:
                print("DEBUG: Looking for meetings at root level...")
            for key in meeting_field_names:
                if key in cache_data:
                    meetings = cache_data[key]
                    found_location = f"root.{key}"
                    if debug:
                        print(f"DEBUG: Found meetings at {found_location}, type: {type(meetings)}, length: {len(meetings) if isinstance(meetings, list) else 'N/A'}")
                    break

        if meetings is None:
            if debug:
                print("DEBUG: No standard keys found at root, looking for any lists...")
            # Look for any list in the cache data that might contain meetings
            for key, value in cache_data.items():
                if isinstance(value, list) and len(value) > 0:
                    # Check if this list contains meeting-like objects
                    first_item = value[0]
                    if isinstance(first_item, dict):
                        # Look for meeting-like fields in the first item
                        meeting_indicators = [
                            'id', 'meeting_id', 'session_id', 'uuid', 'title', 'name', 'subject',
                            'start_time', 'startTime', 'created_at', 'timestamp', 'date',
                            'participants', 'attendees', 'transcript', 'transcription'
                        ]
                        found_indicators = [field for field in meeting_indicators if field in first_item]
                        if found_indicators:
                            meetings = value
                            found_location = f"root.{key}"
                            if debug:
                                print(f"DEBUG: Found potential meetings at {found_location} with indicators: {found_indicators}")
                            break

        # Final fallback: if cache_data itself is a list
        if meetings is None and isinstance(cache_data, list):
            meetings = cache_data
            found_location = "root (entire cache is a list)"
            if debug:
                print(f"DEBUG: Using entire cache as meetings list, length: {len(meetings)}")

        if meetings is None:
            if debug:
                print("DEBUG: No meetings found anywhere in cache structure")
                print(f"DEBUG: Available cache keys: {list(cache_data.keys()) if isinstance(cache_data, dict) else 'Cache is not a dict'}")
            raise GranolaParseError("No meetings found in cache data")

        if not isinstance(meetings, list):
            if debug:
                print(f"DEBUG: Found data at {found_location} but it's not a list: {type(meetings)}")
            raise GranolaParseError("Meetings data must be a list")

        if debug:
            print(f"DEBUG: Successfully found {len(meetings)} meetings at {found_location}")

        return meetings

    def get_meeting_by_id(self, meeting_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific meeting by ID.

        Args:
            meeting_id: The meeting ID to search for

        Returns:
            Optional[Dict[str, Any]]: Meeting object or None if not found
        """
        meetings = self.get_meetings()

        for meeting in meetings:
            if isinstance(meeting, dict):
                # Try different possible ID fields
                for id_field in ['id', 'meeting_id', 'session_id', 'uuid']:
                    if meeting.get(id_field) == meeting_id:
                        return meeting

        return None

    def validate_cache_structure(self) -> bool:
        """
        Validate that the cache has the expected structure.

        Returns:
            bool: True if cache structure is valid
        """
        try:
            cache_data = self.load_cache()
            meetings = self.get_meetings()

            # Basic validation - cache should be a dict and meetings should be a list
            return isinstance(cache_data, dict) and isinstance(meetings, list)

        except Exception:
            return False

    def get_cache_info(self) -> Dict[str, Any]:
        """
        Get information about the cache file and its contents.

        Returns:
            Dict[str, Any]: Cache information
        """
        info = {
            'cache_path': self.cache_path,
            'exists': os.path.exists(self.cache_path),
            'readable': validate_cache_path(self.cache_path),
            'size_bytes': 0,
            'meeting_count': 0,
            'valid_structure': False
        }

        if info['exists']:
            try:
                info['size_bytes'] = os.path.getsize(self.cache_path)
            except Exception:
                pass

        if info['readable']:
            try:
                meetings = self.get_meetings()
                info['meeting_count'] = len(meetings)
                info['valid_structure'] = True
            except Exception:
                pass

        return info

    def reload(self) -> Dict[str, Any]:
        """
        Force reload the cache data.

        Returns:
            Dict[str, Any]: Reloaded cache data
        """
        return self.load_cache(force_reload=True)