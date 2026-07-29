# Unified History MCP

**Config-driven MCP server for cross-domain full-text search** across agent session logs, meeting transcripts, and notification files.

## Quick Start

```bash
pip install unified-history-mcp

# Create a config file at ~/.config/unified-history-mcp/config.toml
# or use the example as a starting point:
cp config.example.toml ~/.config/unified-history-mcp/config.toml

# Start the server
unified-history-mcp
```

Add to your MCP client configuration:

```json
{
  "mcpServers": {
    "unified-history": {
      "command": "unified-history-mcp"
    }
  }
}
```

## Configuration

Configuration is loaded from the first existing location:

1. `$UNIFIED_HISTORY_CONFIG` environment variable
2. `~/.config/unified-history-mcp/config.toml`
3. `./unified-history.toml` (current working directory)

### Domain Configuration

Each `[domains.X]` section defines a searchable domain:

| Field       | Type     | Default      | Description                                    |
|-------------|----------|--------------|------------------------------------------------|
| `dir`       | string   | **required** | Root directory for this domain's files         |
| `pattern`   | string   | `"*"`        | Glob pattern for file discovery                |
| `type`      | string   | `"files"`    | `"files"` or `"dirs"`                          |
| `extensions`| string[] | `[]`         | Allowed extensions (e.g. `[".txt", ".docx"]`)  |
| `extractor` | string   | `"jsonl"`    | Extractor: `jsonl`, `txt`, `transcript`, `notification` |
| `renderer`  | string   | (extractor)  | Renderer override                              |
| `label`     | string   | `"file"`     | Human label: "session", "transcript", etc.     |
| `fst_binary`| string   | `"fst-indexer"` | Path or name of the FST indexer binary     |
| `fst_index_dir` | string | (dir)     | Override for index directory                   |
| `date_field`| string   | —            | JSON field for date extraction (jsonl only)    |
| `filters`   | string[] | `[]`         | Supported filters: `role`, `speaker`           |

### Global Configuration

| Section   | Field  | Description                      |
|-----------|--------|----------------------------------|
| `[history]` | `file` | Path to command history file    |
| `[log]`     | `file` | Path to runtime log file        |

## MCP Tools

### `search(domain, query, ...)`

Full-text search with FST fast path and regex fallback.

| Parameter          | Type     | Default | Description                                      |
|--------------------|----------|---------|--------------------------------------------------|
| `domain`           | string   | `"all"` | Domain or `"all"` for cross-domain               |
| `query`            | string   | `""`    | Search text or regex pattern                     |
| `max_results`      | int      | `20`    | Maximum total matches                            |
| `date_from`        | string   | —       | Start date (YYYY-MM-DD)                          |
| `date_to`          | string   | —       | End date (YYYY-MM-DD, inclusive)                 |
| `regex`            | bool     | `false` | Treat query as regex                             |
| `context_lines`    | int      | `2`     | Surrounding context lines per match              |
| `case_sensitive`   | bool     | `false` | Case-sensitive matching                          |
| `max_matches_per_file` | int  | `5`     | Max matches from any single file                 |
| `role`             | string   | —       | [sessions] Filter by role: user, assistant, tool |
| `speaker`          | string   | —       | [transcripts] Filter by speaker name             |

### `list_domain(domain, date_from, date_to, max_results)`

List available files in a domain with metadata.

| Parameter    | Type   | Default | Description                              |
|--------------|--------|---------|------------------------------------------|
| `domain`     | string | —       | Domain to list                           |
| `date_from`  | string | —       | Start date (YYYY-MM-DD)                  |
| `date_to`    | string | —       | End date (YYYY-MM-DD, inclusive)         |
| `max_results`| int    | `50`    | Maximum entries to show                  |

### `read(domain, id, max_entries, role, speaker)`

Read entries from a domain file.

| Parameter    | Type   | Default | Description                                      |
|--------------|--------|---------|--------------------------------------------------|
| `domain`     | string | —       | Domain                                            |
| `id`         | string | —       | File/directory name or unique prefix              |
| `max_entries`| int    | `50`    | Maximum entries (newest first)                    |
| `role`       | string | —       | [sessions] Filter by role                         |
| `speaker`    | string | —       | [transcripts] Filter by speaker name              |

### `summary(domain, id)`

Get the AI-generated summary for a domain entry.

| Parameter | Type   | Description                              |
|-----------|--------|------------------------------------------|
| `domain`  | string | Domain (sessions, transcripts)           |
| `id`      | string | File/directory name or unique prefix     |

### `rebuild(domain)`

Rebuild FST indexes for configured domains.

| Parameter | Type   | Default | Description             |
|-----------|--------|---------|-------------------------|
| `domain`  | string | `"all"` | Domain or `"all"` for all |

### `search_history(query, max_results, regex, case_sensitive)`

Search the command history file.

| Parameter       | Type    | Default | Description                        |
|-----------------|---------|---------|------------------------------------|
| `query`         | string  | —       | Search text or regex pattern       |
| `max_results`   | int     | `30`    | Maximum matches                    |
| `regex`         | bool    | `false` | Treat query as regex               |
| `case_sensitive`| bool    | `false` | Case-sensitive matching            |

### `search_log(query, max_results, regex, case_sensitive, level)`

Search the runtime log file.

| Parameter       | Type    | Default | Description                        |
|-----------------|---------|---------|------------------------------------|
| `query`         | string  | —       | Search text or regex pattern       |
| `max_results`   | int     | `30`    | Maximum matches                    |
| `regex`         | bool    | `false` | Treat query as regex               |
| `case_sensitive`| bool    | `false` | Case-sensitive matching            |
| `level`         | string  | —       | Filter by log level                |

## How It Works

1. **Configuration** — TOML file defines domains, their directories, extractors, and renderers.
2. **Domain Discovery** — Files are discovered via glob patterns with extension filtering.
3. **Fast Path (FST)** — If the `fst-indexer` binary is installed and indexes are built (via the `rebuild` tool), searches use the blazing-fast FST index.
4. **Slow Path (Regex)** — Falls back to line-by-line regex scanning across files when FST is unavailable.
5. **Extractors** — Produce text entries for FST indexing from different file formats (JSONL, TXT, Tactiq transcripts, notifications).
6. **Renderers** — Format entries for human-readable display in search results, listings, and read output.
