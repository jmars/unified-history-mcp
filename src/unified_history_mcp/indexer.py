"""FST indexer subprocess wrapper.

Interfaces with the `fst-indexer` binary (https://github.com/archiewood/fst-indexer).
"""

import json
import subprocess
from pathlib import Path
from typing import Optional

from .config import DomainConfig


def _iter_domain_files(cfg: DomainConfig) -> list[Path]:
    """Return domain files/dirs, newest first."""
    root = cfg.dir
    if not root.is_dir():
        return []

    if cfg.type == "dirs":
        items = [p for p in root.iterdir() if p.is_dir() and root.name]
        # Apply pattern filtering for dir names
        import fnmatch

        items = [p for p in items if fnmatch.fnmatch(p.name, cfg.pattern)]
    else:
        items = []
        for p in root.rglob(cfg.pattern):
            if p.is_dir():
                continue
            if cfg.extensions and p.suffix.lower() not in cfg.extensions:
                continue
            items.append(p)

    return sorted(
        items, key=lambda p: p.stat().st_mtime if p.exists() else 0, reverse=True
    )


def _files_list_path(index_dir: Path) -> Path:
    """Path to the file list that maps file_idx to actual filenames."""
    return index_dir / "files.json"


def _save_files_list(index_dir: Path, files: list[Path]) -> None:
    """Save the list of indexed files so file_idx can be resolved later."""
    index_dir.mkdir(parents=True, exist_ok=True)
    relative_paths = [str(f.relative_to(f.parent)) for f in files]
    _files_list_path(index_dir).write_text(
        json.dumps(relative_paths, indent=2), encoding="utf-8"
    )


def _load_files_list(index_dir: Path) -> Optional[list[str]]:
    """Load the saved file list. Returns None if not available."""
    fp = _files_list_path(index_dir)
    if not fp.exists():
        return None
    try:
        return json.loads(fp.read_text(encoding="utf-8", errors="replace"))
    except (json.JSONDecodeError, OSError):
        return None


def build_index(cfg: DomainConfig, index_dir: Optional[str] = None) -> tuple[bool, str]:
    """Run fst-indexer build for a domain. Returns (success, message).

    The indexer pipes file contents via stdin to the 'fst-indexer build' command,
    which indexes each entry and writes the FST index to the output directory.
    """
    binary = cfg.fst_binary or "fst-indexer"
    out_dir = Path(index_dir).expanduser().resolve() if index_dir else cfg.effective_index_dir

    # Gather files
    files = _iter_domain_files(cfg)
    if not files:
        return False, f"No files found for domain '{cfg.name}' in {cfg.dir}"

    # Save file list for later resolution
    _save_files_list(out_dir, files)

    try:
        cmd = [
            binary,
            "build",
            "--dir", str(cfg.dir),
            "--pattern", cfg.pattern,
            "--extractor", cfg.extractor,
            "--output", str(out_dir),
        ]
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode == 0:
            return True, f"Index built for '{cfg.name}' ({len(files)} files) at {out_dir}"
        else:
            return False, f"Index build failed for '{cfg.name}': {result.stderr.strip()}"
    except FileNotFoundError:
        return False, f"fst-indexer binary not found: {binary}. Install it from the fst-indexer project."
    except subprocess.TimeoutExpired:
        return False, f"Index build timed out for '{cfg.name}'"
    except OSError as e:
        return False, f"Index build error for '{cfg.name}': {e}"


def search_fst(
    cfg: DomainConfig,
    query: str,
    max_results: int = 100,
    index_dir: Optional[str] = None,
) -> Optional[list[dict]]:
    """Search via FST. Returns list of {file_idx, entry_idx} or None on failure.

    The caller should map file_idx to actual filenames using the saved file list
    for the corresponding index directory.
    """
    binary = cfg.fst_binary or "fst-indexer"
    idx_dir = Path(index_dir).expanduser().resolve() if index_dir else cfg.effective_index_dir
    idx_file = idx_dir / f"{cfg.name}.fst"

    if not idx_file.exists():
        return None

    try:
        cmd = [
            binary,
            "search",
            "-i", str(idx_dir),
            query,
            "--max", str(max_results * 20),  # Fetch extra for post-filtering
            "--json",
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        if result.returncode != 0:
            return None
        data = json.loads(result.stdout)
        return data.get("results", [])
    except (subprocess.TimeoutExpired, json.JSONDecodeError, OSError):
        return None


def resolve_file_idx(index_dir: Path, file_idx: int) -> Optional[str]:
    """Resolve a file_idx to an actual filename using the saved file list."""
    files = _load_files_list(index_dir)
    if files is None or file_idx < 0 or file_idx >= len(files):
        return None
    return files[file_idx]
