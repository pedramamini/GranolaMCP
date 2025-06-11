# Granola.ai JSON Cache Structure Documentation

This document provides a comprehensive analysis of the Granola.ai cache JSON structure based on exploration of the cache file.

## Overview

The Granola.ai cache file (`cache-v3.json`) contains a nested JSON structure with the main data stored under a `cache` key that itself contains a JSON string requiring double parsing.

```python
# Loading pattern
data = json.loads(open("cache-v3.json").read())
cache = json.loads(data['cache'])
```

## Top-Level Structure

The cache contains a `state` object with the following main collections:

```python
cache['state'].keys() = [
    'events',                    # Calendar events
    'panelTemplates',           # UI panel templates
    'people',                   # Contact/participant information
    'calendars',                # Calendar configurations
    'documents',                # Meeting documents/notes
    'sharedDocuments',          # Shared meeting documents
    'documentPanels',           # UI panel configurations
    'transcripts',              # Meeting transcripts
    'meetingsMetadata',         # Meeting metadata
    'featureFlags',             # Application feature flags
    'affinityApiKey',           # Affinity CRM integration
    'affinityDomain',           # Affinity domain configuration
    'highlightSummaryIds',      # Highlighted summary identifiers
    'hidePrivateNoteIds',       # Hidden private note identifiers
    'googleCalendarError',      # Google Calendar sync errors
    'documentListsMetadata',    # Document list metadata
    'documentLists',            # Document organization lists
    'documentListsUnreadStates', # Unread state tracking
    'listsChatHistory',         # Chat history for lists
    'searchChatHistory',        # Search chat history
    'meetingChatHistory',       # Meeting-specific chat history
    'multiChatState',           # Multi-chat state management
    'searchAgentState',         # Search agent state
    'audioInputDeviceName',     # Audio input device configuration
    'lastDocumentSyncTimestamp', # Last sync timestamp
    'lastPreferencesSyncTimestamp', # Last preferences sync
    'generatingPanels',         # Panels being generated
    'comparisonPanelIds',       # Panel comparison identifiers
    'micApps'                   # Microphone app configurations
]
```

## Core Data Structures

### 1. Documents Collection

**Location**: `cache['state']['documents']`

Documents represent individual meetings with their metadata, notes, and configuration.

#### Document Structure

```python
{
    'id': 'uuid-string',                    # Unique meeting identifier
    'created_at': '2025-05-22T19:02:13.254Z',  # ISO 8601 UTC timestamp
    'updated_at': '2025-05-22T20:03:33.981Z',  # Last modification timestamp
    'deleted_at': None,                     # Deletion timestamp (null if active)

    # Meeting Content
    'title': 'Meeting Title',              # Human-readable meeting title
    'notes': {                             # Structured notes (ProseMirror format)
        'type': 'doc',
        'content': [
            {
                'type': 'paragraph',
                'attrs': {
                    'id': 'uuid',
                    'timestamp': None,
                    'timestamp-to': None
                }
            }
        ]
    },
    'notes_plain': '',                     # Plain text version of notes
    'notes_markdown': '',                  # Markdown version of notes
    'overview': None,                      # Meeting overview/summary
    'summary': None,                       # AI-generated summary

    # Meeting Metadata
    'user_id': 'uuid-string',             # Owner user ID
    'type': None,                         # Meeting type classification
    'transcribe': False,                  # Whether to transcribe audio
    'valid_meeting': True,                # Whether this is a valid meeting
    'meeting_end_count': 1,               # Number of times meeting ended
    'creation_source': 'macOS',           # Platform where meeting was created
    'subscription_plan_id': 'granola.plan.free-trial.v1',

    # Privacy & Sharing
    'public': False,                      # Public visibility
    'privacy_mode_enabled': True,         # Privacy mode status
    'show_private_notes': False,          # Show private notes flag
    'has_shareable_link': True,           # Has shareable link
    'sharing_link_visibility': 'public',  # Link visibility level
    'visibility': None,                   # Overall visibility setting

    # Participants
    'people': {
        'creator': {                      # Meeting creator
            'name': 'Full Name',
            'email': 'email@domain.com',
            'details': {
                'person': {
                    'name': {'fullName': 'Full Name'},
                    'avatar': 'https://...',  # Profile image URL
                    'linkedin': {'handle': 'in/username'}
                },
                'company': {'name': 'Company Name'}
            }
        },
        'attendees': []                   # List of meeting attendees
    },

    # Calendar Integration
    'google_calendar_event': None,        # Google Calendar event data

    # External Integrations
    'affinity_note_id': None,            # Affinity CRM note ID
    'hubspot_note_url': None,            # HubSpot note URL
    'external_transcription_id': None,    # External transcription service ID

    # File Attachments
    'attachments': [],                    # File attachments
    'audio_file_handle': None,           # Audio file reference

    # Organization
    'workspace_id': None,                 # Workspace identifier
    'cloned_from': None,                 # Source document if cloned
    'selected_template': None,           # Applied template
    'chapters': None,                    # Meeting chapters/sections
    'status': None,                      # Meeting status
    'notification_config': None          # Notification settings
}
```

### 2. Transcripts Collection

**Location**: `cache['state']['transcripts']`

Transcripts contain the actual spoken content of meetings, segmented by speaker and timestamp.

#### Transcript Structure

Each transcript is an array of transcript segments:

```python
[
    {
        'document_id': 'uuid-string',           # Associated meeting document ID
        'id': 'uuid-string',                    # Unique segment identifier
        'start_timestamp': '2025-05-23T19:57:44.150Z',  # Segment start time (UTC)
        'end_timestamp': '2025-05-23T19:57:47.490Z',    # Segment end time (UTC)
        'text': "Spoken content here",          # Transcribed text
        'source': 'microphone',                # Audio source ('microphone' or 'system')
        'is_final': True                       # Whether transcription is finalized
    },
    # ... more segments
]
```

#### Transcript Sources

- **`microphone`**: Speech from the user's microphone
- **`system`**: Audio from the computer system (other participants, media, etc.)

#### Transcript Processing Notes

1. **Chronological Order**: Segments may not be in perfect chronological order
2. **Overlapping Audio**: Multiple sources can have overlapping timestamps
3. **Finalization**: `is_final` indicates whether the transcription is complete
4. **Stitching Required**: Segments need to be combined for full transcript

### 3. Events Collection

**Location**: `cache['state']['events']`

Events represent calendar events and meeting scheduling information.

### 4. People Collection

**Location**: `cache['state']['people']`

People contains contact information and participant details across all meetings.

### 5. Calendars Collection

**Location**: `cache['state']['calendars']`

Calendar configurations and integration settings.

## Data Relationships

### Document ↔ Transcript Relationship

```python
# Documents and transcripts are linked by ID
document_id = 'uuid-string'
document = cache['state']['documents'][document_id]
transcript = cache['state']['transcripts'][document_id]  # May not exist

# Each transcript segment references its document
for segment in transcript:
    assert segment['document_id'] == document_id
```

### Meeting Lifecycle

1. **Creation**: Document created with basic metadata
2. **Recording**: Transcript segments added in real-time
3. **Processing**: Notes, summaries, and metadata updated
4. **Finalization**: Meeting marked as complete

## Timestamp Handling

### Format
All timestamps use ISO 8601 format with UTC timezone:
```
2025-05-23T19:57:44.150Z
```

### Timezone Conversion
```python
from datetime import datetime
from zoneinfo import ZoneInfo

def utc_to_cst(timestamp_str):
    """Convert UTC timestamp to CST"""
    # Remove 'Z' and parse
    utc_dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
    # Convert to CST
    cst_dt = utc_dt.astimezone(ZoneInfo('America/Chicago'))
    return cst_dt
```

## Data Access Patterns

### Finding Recent Meetings
```python
from datetime import datetime, timedelta

def get_recent_meetings(cache, days=7):
    """Get meetings from the last N days"""
    cutoff = datetime.now() - timedelta(days=days)
    recent = []

    for doc_id, doc in cache['state']['documents'].items():
        created = datetime.fromisoformat(doc['created_at'].replace('Z', '+00:00'))
        if created > cutoff:
            recent.append((doc_id, doc))

    return sorted(recent, key=lambda x: x[1]['created_at'], reverse=True)
```

### Stitching Full Transcript
```python
def stitch_transcript(transcript_segments):
    """Combine transcript segments into full text"""
    # Sort by start timestamp
    sorted_segments = sorted(transcript_segments,
                           key=lambda x: x['start_timestamp'])

    # Group by source and combine text
    full_text = []
    for segment in sorted_segments:
        if segment['is_final']:
            full_text.append(f"[{segment['source']}] {segment['text']}")

    return '\n'.join(full_text)
```

### Meeting Statistics
```python
def get_meeting_stats(cache):
    """Generate meeting statistics"""
    documents = cache['state']['documents']

    stats = {
        'total_meetings': len(documents),
        'meetings_with_transcripts': 0,
        'total_participants': set(),
        'date_range': {'earliest': None, 'latest': None}
    }

    for doc_id, doc in documents.items():
        # Count transcripts
        if doc_id in cache['state']['transcripts']:
            stats['meetings_with_transcripts'] += 1

        # Collect participants
        if 'people' in doc and 'creator' in doc['people']:
            stats['total_participants'].add(doc['people']['creator']['email'])

        # Track date range
        created = doc['created_at']
        if not stats['date_range']['earliest'] or created < stats['date_range']['earliest']:
            stats['date_range']['earliest'] = created
        if not stats['date_range']['latest'] or created > stats['date_range']['latest']:
            stats['date_range']['latest'] = created

    stats['unique_participants'] = len(stats['total_participants'])
    return stats
```

## Notes Format

The `notes` field uses ProseMirror document format:

```json
{
    "type": "doc",
    "content": [
        {
            "type": "paragraph",
            "attrs": {
                "id": "uuid",
                "timestamp": null,
                "timestamp-to": null
            },
            "content": [
                {
                    "type": "text",
                    "text": "Meeting notes content here"
                }
            ]
        }
    ]
}
```

For simpler access, use the `notes_plain` or `notes_markdown` fields.

## Integration Points

### External Services
- **Google Calendar**: `google_calendar_event` field
- **Affinity CRM**: `affinity_note_id` field
- **HubSpot**: `hubspot_note_url` field

### File Storage
- **Audio Files**: Referenced by `audio_file_handle`
- **Attachments**: Listed in `attachments` array

This structure provides a comprehensive foundation for building the GranolaMCP interface to access and manipulate Granola.ai meeting data programmatically.