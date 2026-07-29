"""Tests for server helpers — path traversal rejection in _resolve_file."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from unified_history_mcp.config import DomainConfig
from unified_history_mcp.server import _resolve_file


def _make_cfg(dir_path: Path, type_: str = "files") -> DomainConfig:
    """Helper to build a DomainConfig for testing."""
    return DomainConfig(
        name="test",
        dir=dir_path,
        type=type_,
        pattern="*",
        extensions=[],
        extractor="jsonl",
        label="file",
    )


class TestResolveFile:
    """_resolve_file path traversal rejection."""

    def test_rejects_dotdot_in_id(self, tmp_path: Path) -> None:
        """IDs containing '..' are rejected (path traversal)."""
        # ".." in Path(id).parts means any component is exactly ".."
        cfg = _make_cfg(tmp_path)
        result = _resolve_file(cfg, "..")
        assert result is None

    def test_rejects_dotdot_in_subpath(self, tmp_path: Path) -> None:
        """IDs with embedded .. are rejected."""
        cfg = _make_cfg(tmp_path)
        result = _resolve_file(cfg, "subdir/../../etc/passwd")
        assert result is None

    def test_rejects_absolute_path(self, tmp_path: Path) -> None:
        """IDs starting with / are rejected."""
        cfg = _make_cfg(tmp_path)
        result = _resolve_file(cfg, "/etc/passwd")
        assert result is None

    def test_returns_none_when_no_matches(self, tmp_path: Path) -> None:
        """When glob finds no candidates, None is returned."""
        cfg = _make_cfg(tmp_path)
        result = _resolve_file(cfg, "nonexistent_file.txt")
        assert result is None

    def test_resolves_valid_file(self, tmp_path: Path) -> None:
        """A valid file within the domain dir is resolved correctly."""
        sub = tmp_path / "subdir"
        sub.mkdir()
        target = sub / "test_file.txt"
        target.write_text("hello", encoding="utf-8")

        cfg = _make_cfg(tmp_path)
        result = _resolve_file(cfg, "test_file.txt")
        assert result is not None
        assert result.name == "test_file.txt"

    def test_resolves_with_extension(self, tmp_path: Path) -> None:
        """A file with known extension is found precisely."""
        target = tmp_path / "data.jsonl"
        target.write_text("{}", encoding="utf-8")

        cfg = _make_cfg(tmp_path)
        result = _resolve_file(cfg, "data.jsonl")
        assert result is not None
        assert result.name == "data.jsonl"

    def test_returns_none_when_path_escapes_domain_dir(self, tmp_path: Path) -> None:
        """If glob finds a candidate but it resolves outside domain dir, None."""
        outside = tmp_path / "outside"
        outside.mkdir()
        (outside / "evil.txt").write_text("gotcha", encoding="utf-8")

        # Create a symlink inside the domain dir pointing outside
        inside = tmp_path / "inside"
        inside.mkdir()
        link = inside / "link"
        try:
            link.symlink_to(outside)
        except OSError:
            pytest.skip("Cannot create symlinks on this platform")

        cfg = _make_cfg(inside)
        # The link itself is inside, but resolved path would escape
        # _resolve_file checks resolved.is_relative_to(cfg.dir.resolve())
        # Actually, the glob searches inside/ for files — the symlink target
        # is a dir, not a file, so it won't match the file extension check.
        # Let's test directly: create a symlink to a *file* inside
        evil_file = outside / "evil.txt"
        link_to_file = inside / "evil.txt"
        try:
            link_to_file.symlink_to(evil_file)
        except OSError:
            pytest.skip("Cannot create symlinks on this platform")

        result = _resolve_file(cfg, "evil.txt")
        # The rglob finds "inside/evil.txt", which resolves to the outside path
        # resolved.is_relative_to(cfg.dir.resolve()) should be False
        assert result is None

    def test_resolves_dir_type(self, tmp_path: Path) -> None:
        """For type='dirs', _resolve_file uses dir.glob instead of rglob."""
        sub = tmp_path / "mydir"
        sub.mkdir()
        (sub / "some_file.txt").write_text("data", encoding="utf-8")

        cfg = _make_cfg(tmp_path, type_="dirs")
        result = _resolve_file(cfg, "mydir")
        assert result is not None
        assert result.name == "mydir"
        assert result.is_dir()
