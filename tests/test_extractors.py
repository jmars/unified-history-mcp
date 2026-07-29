"""Tests for extractor functions."""

import json

import pytest

from unified_history_mcp.extractors import (
    extract_jsonl,
    extract_txt,
    extract_transcript,
    extract_notification,
)


class TestExtractJsonl:
    """extract_jsonl behaviour."""

    def test_extracts_content_fields(self, sample_jsonl: str) -> None:
        """Content fields from JSONL messages are extracted."""
        entries = extract_jsonl(sample_jsonl)
        # First line has content
        assert any("Hello, can you help me?" in e for e in entries)
        # Second line has content
        assert any("Sure, what do you need?" in e for e in entries)

    def test_extracts_tool_call_names(self, sample_jsonl: str) -> None:
        """Lines with tool_calls (no content) produce function name entries."""
        entries = extract_jsonl(sample_jsonl)
        assert any("get_weather" in e for e in entries)

    def test_handles_non_json_lines(self, sample_jsonl: str) -> None:
        """Non-JSON lines are included as-is (truncated to 1000)."""
        entries = extract_jsonl(sample_jsonl)
        assert any("not valid json at all" in e for e in entries)

    def test_empty_content_produces_placeholder(self, sample_jsonl: str) -> None:
        """A JSON line with empty content and no tool_calls -> '(no content)'."""
        entries = extract_jsonl(sample_jsonl)
        assert any(e == "(no content)" for e in entries)

    def test_empty_text_returns_empty_list(self) -> None:
        """Empty input returns an empty list."""
        assert extract_jsonl("") == []

    def test_only_blank_lines(self) -> None:
        """All-blank input returns an empty list."""
        assert extract_jsonl("\n\n  \n") == []


class TestExtractTxt:
    """extract_txt behaviour."""

    def test_returns_non_empty_lines(self, sample_txt: str) -> None:
        """Each non-empty line is an entry."""
        entries = extract_txt(sample_txt)
        assert "Line one of text." in entries
        assert "Line two of text." in entries
        assert "Line three with some space around it." in entries

    def test_skips_blank_lines(self, sample_txt: str) -> None:
        """Blank lines are excluded."""
        entries = extract_txt(sample_txt)
        # There are blank lines in sample_txt — they should be skipped
        assert "" not in entries

    def test_empty_text(self) -> None:
        """Empty input returns empty list."""
        assert extract_txt("") == []

    def test_all_blank_lines(self) -> None:
        """All-blank input returns empty list."""
        assert extract_txt("\n\n\n") == []


class TestExtractTranscript:
    """extract_transcript behaviour."""

    def test_returns_speaker_text_entries(self, sample_transcript_text: str) -> None:
        """Each turn yields a 'speaker: text' entry."""
        entries = extract_transcript(sample_transcript_text)
        # Expect 3 turns
        assert len(entries) == 3

        assert entries[0].startswith("Alice:")
        assert "Good morning everyone." in entries[0]

        assert entries[1].startswith("Bob:")
        assert "I finished the feature work" in entries[1]

        assert entries[2].startswith("Charlie:")
        assert "Sounds good." in entries[2]

    def test_empty_text(self) -> None:
        """Empty transcript returns empty list."""
        assert extract_transcript("") == []

    def test_no_speaker_turns(self) -> None:
        """Text without speaker headers returns empty list."""
        text = "Some random text\nWithout any speaker turns\n"
        assert extract_transcript(text) == []


class TestExtractNotification:
    """extract_notification behaviour."""

    def test_extracts_summary_and_body(self, sample_notification_jsonl: str) -> None:
        """Summary and body are extracted from JSONL notification entries."""
        entries = extract_notification(sample_notification_jsonl)

        # First entry: summary + body
        assert any("PR Approved" in e for e in entries)
        assert any("Your pull request #42 was merged" in e for e in entries)

        # Second entry: Build Failed + body
        assert any("Build Failed" in e for e in entries)
        assert any("Pipeline failed on main branch" in e for e in entries)

    def test_body_only_notification(self, sample_notification_jsonl: str) -> None:
        """Notification with only body still extracts."""
        entries = extract_notification(sample_notification_jsonl)
        assert any("Notification without summary" in e for e in entries)

    def test_summary_only_notification(self, sample_notification_jsonl: str) -> None:
        """Notification with only summary still extracts."""
        entries = extract_notification(sample_notification_jsonl)
        assert any("Just summary" in e for e in entries)

    def test_handles_non_json_lines(self, sample_notification_jsonl: str) -> None:
        """Non-JSON lines are included as-is."""
        entries = extract_notification(sample_notification_jsonl)
        assert any("bad json line" in e for e in entries)

    def test_empty_text(self) -> None:
        """Empty input returns empty list."""
        assert extract_notification("") == []

    def test_only_blank_lines(self) -> None:
        """All-blank input returns empty list."""
        assert extract_notification("\n\n\n") == []
