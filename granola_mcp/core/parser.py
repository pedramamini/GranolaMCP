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
            List[Dict[str, Any]]: List of meeting objects (combined documents and metadata)

        Raises:
            GranolaParseError: If cache cannot be loaded or meetings not found
        """
        cache_data = self.load_cache()

        if debug:
            print(f"DEBUG: Cache data keys: {list(cache_data.keys())}")

        # Look for the 'state' key (Granola v3 format)
        if 'state' not in cache_data:
            raise GranolaParseError("Cache data missing required 'state' key")

        state_data = cache_data['state']
        if debug:
            print(f"DEBUG: Found 'state' key with keys: {list(state_data.keys())}")

        # Get documents (main meeting data)
        documents = state_data.get('documents', {})
        if debug:
            print(f"DEBUG: Found {len(documents)} documents")

        # Get meeting metadata (additional info)
        meetings_metadata = state_data.get('meetingsMetadata', {})
        if debug:
            print(f"DEBUG: Found {len(meetings_metadata)} meeting metadata entries")

        # Get transcripts
        transcripts = state_data.get('transcripts', {})
        if debug:
            print(f"DEBUG: Found {len(transcripts)} transcripts")

        # Get document panels (contains structured notes)
        document_panels = state_data.get('documentPanels', {})
        if debug:
            print(f"DEBUG: Found {len(document_panels)} document panels")

        # Get document lists (folders) for organization
        document_lists = state_data.get('documentLists', {})
        document_lists_metadata = state_data.get('documentListsMetadata', {})
        if debug:
            print(f"DEBUG: Found {len(document_lists)} document lists/folders")

        # Create reverse mapping: meeting_id -> folder_info
        meeting_to_folder = {}
        for list_id, meeting_ids in document_lists.items():
            folder_info = document_lists_metadata.get(list_id, {})
            folder_name = folder_info.get('title', 'Unknown')
            for meeting_id in meeting_ids:
                meeting_to_folder[meeting_id] = {
                    'folder_id': list_id,
                    'folder_name': folder_name
                }

        # Combine documents with their metadata, transcripts, and panels
        meetings = []
        for doc_id, doc_data in documents.items():
            # Start with document data
            meeting = doc_data.copy()
            
            # Add metadata if available
            if doc_id in meetings_metadata:
                meta = meetings_metadata[doc_id]
                # Only add metadata fields that don't conflict with document fields
                for key, value in meta.items():
                    if key not in meeting or not meeting[key]:
                        meeting[key] = value

            # Add transcript if available
            if doc_id in transcripts:
                meeting['transcript_data'] = transcripts[doc_id]

            # Add document panels content (AI summaries and structured notes)
            if doc_id in document_panels:
                panels = document_panels[doc_id]
                
                # Extract AI summaries from original_content (HTML format)
                ai_summaries = []
                for panel_id, panel_data in panels.items():
                    original_content = panel_data.get('original_content', '')
                    if original_content and isinstance(original_content, str):
                        # Skip panels that are just links
                        if not original_content.strip().startswith('<hr>'):
                            ai_summaries.append(original_content)
                
                if ai_summaries:
                    # Combine all AI summaries into one
                    meeting['ai_summary_html'] = '\n\n'.join(ai_summaries)
                
                # Look for the first panel with structured content (for fallback)
                for panel_id, panel_data in panels.items():
                    panel_content = panel_data.get('content')
                    if panel_content and isinstance(panel_content, dict):
                        meeting['panel_content'] = panel_content
                        break

            # Add folder information
            if doc_id in meeting_to_folder:
                folder_info = meeting_to_folder[doc_id]
                meeting['folder_name'] = folder_info['folder_name']
                meeting['folder_id'] = folder_info['folder_id']
            else:
                meeting['folder_name'] = None
                meeting['folder_id'] = None

            meetings.append(meeting)

        if debug:
            print(f"DEBUG: Successfully created {len(meetings)} combined meeting objects")

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