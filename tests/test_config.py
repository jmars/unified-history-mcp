"""Tests for config loading, domain parsing, and path resolution."""

import os
from pathlib import Path

import pytest

from unified_history_mcp.config import Config, DomainConfig, load_config


class TestDomainConfig:
    """DomainConfig dataclass behaviour."""

    def test_expands_tilde_in_dir(self) -> None:
        """Domain dir with ~ is expanded to the user's home directory."""
        cfg = DomainConfig(name="test", dir="~/somewhere")
        home = Path.home().resolve()
        assert str(cfg.dir).startswith(str(home))
        assert "somewhere" in str(cfg.dir)

    def test_effective_renderer_defaults_to_extractor(self) -> None:
        """When renderer is not set, effective_renderer returns the extractor."""
        cfg = DomainConfig(name="test", dir="/tmp", extractor="jsonl")
        assert cfg.effective_renderer == "jsonl"

    def test_effective_renderer_uses_custom_renderer(self) -> None:
        """When renderer is set, effective_renderer returns it."""
        cfg = DomainConfig(name="test", dir="/tmp", extractor="jsonl", renderer="custom")
        assert cfg.effective_renderer == "custom"

    def test_effective_index_dir_defaults_to_domain_dir(self) -> None:
        """When fst_index_dir is not set, effective_index_dir is the domain dir."""
        cfg = DomainConfig(name="test", dir="/tmp/mydir")
        assert cfg.effective_index_dir == cfg.dir

    def test_effective_index_dir_uses_custom(self) -> None:
        """When fst_index_dir is set, effective_index_dir returns it."""
        cfg = DomainConfig(
            name="test", dir="/tmp/mydir", fst_index_dir="/tmp/index"
        )
        expected = Path("/tmp/index").resolve()
        assert cfg.effective_index_dir == expected

    def test_default_type(self) -> None:
        """Default type is 'files'."""
        cfg = DomainConfig(name="test", dir="/tmp")
        assert cfg.type == "files"

    def test_default_extractor(self) -> None:
        """Default extractor is 'jsonl'."""
        cfg = DomainConfig(name="test", dir="/tmp")
        assert cfg.extractor == "jsonl"

    def test_default_filters_empty(self) -> None:
        """Filters default to an empty list."""
        cfg = DomainConfig(name="test", dir="/tmp")
        assert cfg.filters == []


class TestLoadConfig:
    """load_config() behaviour."""

    def test_no_config_file_returns_empty(self) -> None:
        """load_config with non-existent path returns empty Config."""
        cfg = load_config(Path("/nonexistent/path/config.toml"))
        assert cfg.domains == {}
        assert cfg.history_file is None
        assert cfg.log_file is None

    def test_valid_toml_creates_domain_configs(self, tmp_path: Path) -> None:
        """A valid TOML creates correct DomainConfig objects."""
        # Create a dummy domain dir so _resolve_path works
        domain_dir = tmp_path / "sessions"
        domain_dir.mkdir()

        config_path = tmp_path / "config.toml"
        config_path.write_text(
            f'[domains.sessions]\n'
            f'dir = "{domain_dir}"\n'
            f'pattern = "*.jsonl"\n'
            f'type = "files"\n'
            f'extensions = [".jsonl"]\n'
            f'extractor = "jsonl"\n'
            f'label = "session"\n'
            f'filters = ["role"]\n'
            f'\n'
            f'[history]\n'
            f'file = "{tmp_path}/history.txt"\n'
            f'\n'
            f'[log]\n'
            f'file = "{tmp_path}/vibe.log"\n'
            ,
            encoding="utf-8",
        )
        cfg = load_config(config_path)

        assert "sessions" in cfg.domains
        d = cfg.domains["sessions"]
        assert d.name == "sessions"
        assert d.dir == domain_dir.resolve()
        assert d.pattern == "*.jsonl"
        assert d.type == "files"
        assert d.extensions == [".jsonl"]
        assert d.extractor == "jsonl"
        assert d.label == "session"
        assert d.filters == ["role"]
        assert d.renderer == ""
        assert d.fst_binary == "fst-indexer"

        assert cfg.history_file == (tmp_path / "history.txt").resolve()
        assert cfg.log_file == (tmp_path / "vibe.log").resolve()

    def test_default_values_in_toml(self, tmp_path: Path) -> None:
        """Domain values omitted from TOML receive sensible defaults."""
        domain_dir = tmp_path / "mydomain"
        domain_dir.mkdir()

        config_path = tmp_path / "config.toml"
        config_path.write_text(
            f'[domains.mydomain]\n'
            f'dir = "{domain_dir}"\n',
            encoding="utf-8",
        )
        cfg = load_config(config_path)

        d = cfg.domains["mydomain"]
        assert d.pattern == "*"
        assert d.type == "files"
        assert d.extensions == []
        assert d.extractor == "jsonl"
        assert d.renderer == ""
        assert d.label == "file"
        assert d.filters == []

    def test_history_and_log_not_required(self, tmp_path: Path) -> None:
        """Config without [history] and [log] sections still works."""
        domain_dir = tmp_path / "mydomain"
        domain_dir.mkdir()

        config_path = tmp_path / "config.toml"
        config_path.write_text(
            f'[domains.mydomain]\n'
            f'dir = "{domain_dir}"\n',
            encoding="utf-8",
        )
        cfg = load_config(config_path)
        assert cfg.history_file is None
        assert cfg.log_file is None

    def test_filters_parsed_correctly(self, tmp_path: Path) -> None:
        """Filters list is parsed from TOML."""
        domain_dir = tmp_path / "mydomain"
        domain_dir.mkdir()

        config_path = tmp_path / "config.toml"
        config_path.write_text(
            f'[domains.mydomain]\n'
            f'dir = "{domain_dir}"\n'
            f'filters = ["role", "speaker"]\n',
            encoding="utf-8",
        )
        cfg = load_config(config_path)
        assert cfg.domains["mydomain"].filters == ["role", "speaker"]

    def test_path_expansion_in_config(self, tmp_path: Path, monkeypatch) -> None:
        """Tilde in dir paths is expanded."""
        monkeypatch.delenv("UNIFIED_HISTORY_CONFIG", raising=False)

        config_path = tmp_path / "config.toml"
        config_path.write_text(
            '[domains.test]\n'
            'dir = "~/test-domain"\n',
            encoding="utf-8",
        )
        cfg = load_config(config_path)
        home = Path.home().resolve()
        assert str(cfg.domains["test"].dir).startswith(str(home))
        assert "test-domain" in str(cfg.domains["test"].dir)

    def test_unified_history_config_env_var(self, tmp_path: Path, monkeypatch) -> None:
        """The UNIFIED_HISTORY_CONFIG env var overrides default config path."""
        domain_dir = tmp_path / "logs"
        domain_dir.mkdir()

        config_path = tmp_path / "my-config.toml"
        config_path.write_text(
            f'[domains.logs]\n'
            f'dir = "{domain_dir}"\n',
            encoding="utf-8",
        )
        monkeypatch.setenv("UNIFIED_HISTORY_CONFIG", str(config_path))
        cfg = load_config()
        assert "logs" in cfg.domains
        assert cfg.domains["logs"].dir == domain_dir.resolve()
