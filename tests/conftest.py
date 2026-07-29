"""Shared fixtures for unified-history-mcp tests."""

import json
from pathlib import Path

import pytest


# ---------------------------------------------------------------------------
# Sample data
# ---------------------------------------------------------------------------

SAMPLE_JSONL = (
    '{"role": "user", "content": "Hello, can you help me?"}\n'
    '{"role": "assistant", "content": "Sure, what do you need?"}\n'
    '{"role": "tool", "tool_calls": [{"function": {"name": "get_weather"}}]}\n'
    "not valid json at all\n"
    '{"role": "user", "content": ""}\n'
)

SAMPLE_TXT = """Line one of text.
Line two of text.

Line three with some space around it.
"""

SAMPLE_TRANSCRIPT_TXT = """Meeting: Weekly Sync
Date: 2026-01-15 10:00
Duration: 45m
Platform: MS_TEAMS
Participants: Alice, Bob, Charlie
================================================================
Alice (10:00:15)
Good morning everyone.
Let's start with the updates.

Bob (10:01:30)
I finished the feature work yesterday.
Just need to write tests.

Charlie (10:02:45)
Sounds good. I'll review the PR.
Any blockers for the release?
"""

# A JSONL notification sample
SAMPLE_NOTIFICATION_JSONL = (
    '{"summary": "PR Approved", "body": "Your pull request #42 was merged.", "timestamp": "2026-01-15T10:00:00Z"}\n'
    '{"summary": "Build Failed", "body": "Pipeline failed on main branch."}\n'
    '{"body": "Notification without summary"}\n'
    '{"summary": "Just summary"}\n'
    "bad json line\n"
)


@pytest.fixture
def temp_data_dir(tmp_path: Path) -> Path:
    """Create a temp directory with sample data files for extraction tests."""
    d = tmp_path / "data"
    d.mkdir()

    # messages.jsonl
    (d / "messages.jsonl").write_text(SAMPLE_JSONL, encoding="utf-8")

    # notes.txt
    (d / "notes.txt").write_text(SAMPLE_TXT, encoding="utf-8")

    # transcript.txt
    (d / "transcript.txt").write_text(SAMPLE_TRANSCRIPT_TXT, encoding="utf-8")

    # notifications.jsonl
    (d / "notifications.jsonl").write_text(SAMPLE_NOTIFICATION_JSONL, encoding="utf-8")

    return d


@pytest.fixture
def sample_jsonl() -> str:
    return SAMPLE_JSONL


@pytest.fixture
def sample_txt() -> str:
    return SAMPLE_TXT


@pytest.fixture
def sample_transcript_text() -> str:
    return SAMPLE_TRANSCRIPT_TXT


@pytest.fixture
def sample_notification_jsonl() -> str:
    return SAMPLE_NOTIFICATION_JSONL
