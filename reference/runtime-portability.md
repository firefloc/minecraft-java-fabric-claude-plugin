# Runtime portability

The implementation is shared between Claude Code, Codex and Hermes Agent.
Host-specific metadata belongs at the edges; the Minecraft workflow and tool
surface stay in the shared `skills/`, `reference/`, and `tools/` trees.

## Host surface: one contract, three adapters

Shared instructions name a **server** plus the **native Java tool name**
(`minecraft-java` + `server_get_status`, `minecraft-java-client` +
`view_capture`). They never hardcode a host's prefixed spelling: each host
resolves the name it actually discovered.

| | Claude Code | Codex | Hermes Agent |
| --- | --- | --- | --- |
| Plugin root | directory containing `.claude-plugin/plugin.json`; Claude expands `${CLAUDE_PLUGIN_ROOT}` when a skill runs | directory containing `.codex-plugin/plugin.json`, or the repository checkout | the clone itself; `skills/` is registered through `skills.external_dirs` |
| `server_get_status` | `mcp__minecraft-java__server_get_status` | the same shape, resolved by Codex | `mcp__minecraft_java__server_get_status` |
| `view_capture` | `mcp__minecraft-java-client__view_capture` | the same shape, resolved by Codex | `mcp__minecraft_java_client__view_capture` |
| Ask a question | the `AskUserQuestion` tool | ask in the conversation | ask in the conversation (the active interface's clarification prompt) |
| No sub-agent | inline, or `context: fork` in Claude metadata | current conversation, or a native Codex subagent when available | current conversation, or `delegate_task` when available |

Hermes normalizes every MCP server and tool name to `[A-Za-z0-9_]`, so the two
hyphens in `minecraft-java-client` become underscores. The expected Hermes
prefixes above are a prediction from that rule; **the host's actual discovery
stays the authority** — if `hermes skills` or a session lists a different
spelling, that spelling wins. Local Hermes skills take precedence over
`external_dirs` entries on a name collision, so a conflicting local skill must
be detected rather than silently shadowing a shared one.

No delegation facility on the active host means the phases run sequentially in
one conversation. It never means a gate is dropped.

## Plugin root and paths

The plugin root is the directory containing `.claude-plugin/plugin.json` or
`.codex-plugin/plugin.json`.

Claude Code legacy instructions use the `${CLAUDE_PLUGIN_ROOT}` token because
Claude expands it when a skill runs. Codex and Hermes do not define that token.
Outside an explicitly Claude-labelled instruction, resolve the root from the
installed plugin package or the repository checkout and pass an absolute,
quoted path to a helper — a checkout path may contain spaces. Never send the
literal token to a shell or Python process.

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
