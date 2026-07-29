"""Tests for transcript parsing."""

from datetime import datetime
from pathlib import Path

from unified_history_mcp.transcript import (
    parse_transcript,
    read_transcript_text,
    parse_transcript_file,
)


# A more complex sample with multi-line turns and metadata
COMPLEX_TRANSCRIPT = """Meeting: Architecture Review
Date: 2026-02-10 14:00
Duration: 1h 15m
Platform: GOOGLE_MEET
Participants: Alice, Bob, Charlie, Diana
================================================================
Alice (14:00:05)
Let's go through the architecture proposal.
I've shared my screen.

Bob (14:02:30)
The proposal looks solid overall.
One concern is the caching layer.
We should consider Redis instead.

Charlie (14:05:00)
Redis would add operational complexity.
Let's discuss offline.

Diana (14:06:15)
+1 for discussing offline.
Let's focus on the API contracts first.
"""

# Minimal transcript — just header and one turn
MINIMAL_TRANSCRIPT = """Meeting: Quick Sync
Date: 2026-03-01 09:30
Duration: 15m
Platform: MS_TEAMS
Participants: Alice
================================================================
Alice (09:30:00)
Quick check-in.
"""

# No header separator (no === line)
NO_HEADER_TRANSCRIPT = """Alice (10:00:00)
Hello there.

Bob (10:01:00)
Hi Alice!
"""


class TestParseTranscript:
    """parse_transcript() behaviour."""

    def test_parses_complete_transcript(self) -> None:
        """Full transcript is parsed into structured data."""
        result = parse_transcript(COMPLEX_TRANSCRIPT)

        assert result["meeting"] == "Architecture Review"
        assert isinstance(result["meeting_date"], datetime)
        assert result["meeting_date"].year == 2026
        assert result["meeting_date"].month == 2
        assert result["meeting_date"].day == 10
        assert result["duration"] == "1h 15m"
        assert result["platform"] == "GOOGLE_MEET"
        assert result["participants"] == ["Alice", "Bob", "Charlie", "Diana"]

    def test_parses_speaker_turns(self) -> None:
        """Speaker turns have correct names, timestamps, and multi-line text."""
        result = parse_transcript(COMPLEX_TRANSCRIPT)
        turns = result["turns"]
        assert len(turns) == 4

        # Alice turn
        assert turns[0]["speaker"] == "Alice"
        assert turns[0]["timestamp"] == "14:00:05"
        assert "Let's go through the architecture proposal" in turns[0]["text"]
        assert "I've shared my screen." in turns[0]["text"]

        # Bob turn (multi-line)
        assert turns[1]["speaker"] == "Bob"
        assert turns[1]["timestamp"] == "14:02:30"
        assert "The proposal looks solid overall." in turns[1]["text"]
        assert "We should consider Redis instead." in turns[1]["text"]

        # Charlie turn
        assert turns[2]["speaker"] == "Charlie"
        assert turns[2]["timestamp"] == "14:05:00"
        assert "Redis would add operational complexity." in turns[2]["text"]

        # Diana turn
        assert turns[3]["speaker"] == "Diana"
        assert turns[3]["timestamp"] == "14:06:15"
        assert "+1 for discussing offline." in turns[3]["text"]

    def test_line_numbers_in_turns(self) -> None:
        """Each turn tracks its start and end line numbers."""
        result = parse_transcript(COMPLEX_TRANSCRIPT)
        for turn in result["turns"]:
            assert turn["line_start"] >= 0
            assert turn["line_end"] >= turn["line_start"]

    def test_minimal_transcript(self) -> None:
        """A minimal single-turn transcript parses correctly."""
        result = parse_transcript(MINIMAL_TRANSCRIPT)
        assert result["meeting"] == "Quick Sync"
        assert result["platform"] == "MS_TEAMS"
        assert len(result["turns"]) == 1
        assert result["turns"][0]["speaker"] == "Alice"
        assert result["turns"][0]["text"] == "Quick check-in."

    def test_no_header_separator(self) -> None:
        """Transcript without === header separator still parses turns."""
        result = parse_transcript(NO_HEADER_TRANSCRIPT)
        # No metadata can be extracted without header
        assert result["meeting"] is None
        assert result["meeting_date"] is None
        # But turns are still parsed
        assert len(result["turns"]) == 2
        assert result["turns"][0]["speaker"] == "Alice"
        assert result["turns"][1]["speaker"] == "Bob"

    def test_empty_text(self) -> None:
        """Empty text returns empty structure with no turns."""
        result = parse_transcript("")
        assert result["turns"] == []
        assert result["participants"] == []
        assert result["meeting"] is None

    def test_raw_lines_present(self) -> None:
        """Raw input lines are stored in raw_lines."""
        result = parse_transcript(MINIMAL_TRANSCRIPT)
        assert len(result["raw_lines"]) > 0
        assert any("Quick Sync" in line for line in result["raw_lines"])


class TestReadTranscriptText:
    """read_transcript_text() behaviour."""

    def test_reads_txt_file(self, tmp_path: Path) -> None:
        """A .txt file is read as UTF-8 text."""
        p = tmp_path / "meeting.txt"
        p.write_text(COMPLEX_TRANSCRIPT, encoding="utf-8")
        text = read_transcript_text(p)
        assert "Architecture Review" in text
        assert "Redis would add operational complexity" in text

    def test_nonexistent_file_returns_empty(self, tmp_path: Path) -> None:
        """Non-existent file returns empty string."""
        p = tmp_path / "doesnotexist.txt"
        text = read_transcript_text(p)
        assert text == ""

    def test_docx_suffix_returns_empty_for_non_docx(self, tmp_path: Path) -> None:
        """A .docx that isn't actually a zip returns empty."""
        p = tmp_path / "meeting.docx"
        p.write_text("this is not a zip file", encoding="utf-8")
        text = read_transcript_text(p)
        assert text == ""


class TestParseTranscriptFile:
    """parse_transcript_file() behaviour."""

    def test_works_on_real_file(self, tmp_path: Path) -> None:
        """Parsing a .txt file works end-to-end."""
        p = tmp_path / "meeting.txt"
        p.write_text(COMPLEX_TRANSCRIPT, encoding="utf-8")
        result = parse_transcript_file(p)
        assert result["meeting"] == "Architecture Review"
        assert len(result["turns"]) == 4
        assert result["participants"] == ["Alice", "Bob", "Charlie", "Diana"]

    def test_returns_deep_copy(self, tmp_path: Path) -> None:
        """parse_transcript_file returns mutable copies (not the cached object)."""
        p = tmp_path / "meeting.txt"
        p.write_text(MINIMAL_TRANSCRIPT, encoding="utf-8")
        result1 = parse_transcript_file(p)
        result2 = parse_transcript_file(p)
        # Both should be independent copies
        assert result1["participants"] == result2["participants"]
        # Modifying one should not affect the other
        result1["participants"].append("Bob")
        assert len(result2["participants"]) == 1
