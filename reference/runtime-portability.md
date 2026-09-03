# Runtime portability

The implementation is shared between Claude Code and Codex. Host-specific
metadata belongs at the edges; the Minecraft workflow and tool surface stay in
the shared `skills/`, `reference/`, and `tools/` trees.

## Plugin root and paths

The plugin root is the directory containing `.claude-plugin/plugin.json` or
`.codex-plugin/plugin.json`.

Claude Code legacy instructions use the `${CLAUDE_PLUGIN_ROOT}` token because
Claude expands it when a skill runs. Codex does not define that token. In Codex,
resolve a reference from the installed plugin package or repository checkout,
and pass an absolute path (or a path relative to the current checkout) to a
helper. Never send the literal token to a shell or Python process.

The bundled Python helpers discover their own package location and share MCP
configuration logic in `tools/mcp_config.py`; they do not require a host
environment variable for the plugin root.

## Model and delegation roles

Shared workflow instructions use these logical roles:

| Role | Meaning | Claude compatibility | Codex behavior |
| --- | --- | --- | --- |
| `lead` | Routing, planning, design judgment | historical Opus metadata | current configured model with strong reasoning |
| `specialist` | Research, terrain, inspection, blueprint work | historical Sonnet metadata | current configured model or a native subagent |
| `executor` | Bounded plan execution | historical Haiku metadata | fast/native subagent when available; otherwise sequential |
| `host-default` | Interactive setup and connection | inherited model | current configured model |

The old `model`, `context`, `effort`, and `color` fields remain only where
Claude Code needs them. They are not a Codex model contract. Codex entry skills
must not select a Claude model name; they preserve inline versus delegated work
through the Codex conversation and native subagent facilities when available.

## MCP invariants

The two HTTP MCP servers retain their established names and tool names:

- `minecraft-java` — world reads and writes, normally port 8765;
- `minecraft-java-client` — optional rendered-player perception and capture,
  normally port 8766.

The Codex manifest supplies no-auth localhost defaults. Remote/authenticated
setups use an environment-backed bearer token; see
`reference/mcp/codex-connection.md`. The config reader also accepts Claude's
JSON settings, Codex's TOML settings, and the existing project `.mcp.json`.
