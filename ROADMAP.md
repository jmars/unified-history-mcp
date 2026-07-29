# Roadmap

## Non-Goals (v1)

The following are explicitly out of scope for v1:

- **Auto-summary generation** — separate concern, handled by other services
- **Web UI** — MCP tools are the only interface
- **Plug-in extractor/renderer system via entry_points** — v1 uses built-in extractors/renderers only
- **Completely config-driven rendering** — if/elif chains are acceptable for v1; renderers are hardcoded per extractor type
- **File watcher for automatic reindexing** — `rebuild` tool must be called explicitly

## Future Directions

- Pluggable extractor/renderer system
- Deferred index building (background rebuild)
- Multi-user namespace support
- Config merge from multiple files
