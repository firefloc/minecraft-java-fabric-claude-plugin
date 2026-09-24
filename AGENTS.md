# AGENTS.md

This repository ships one Minecraft Java workflow with three host adapters:

- Claude Code: `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`,
  `CLAUDE.md`, and the existing `agents/*.md` files.
- Codex: `.codex-plugin/plugin.json`, `agents/openai.yaml`, the two compact
  agent adapters under `agents/codex-*.md`, and the two thin entry skills
  `minecraft-builder` and `minecraft-mcp-setup`.
- Hermes Agent: no manifest of its own — the profile registers this checkout's
  `skills/` through `skills.external_dirs` and the two servers through
  `mcp_servers`. See `reference/mcp/hermes-connection.md`.

The `skills/` tree, `reference/` tree, `tools/` tree, MCP server names, and Java
tool names are shared. Never copy the suite per host and never fork the builder
logic just to change host syntax; keep each host's surface intact when changing
another's adapter.

## Runtime rules

Read `reference/runtime-portability.md` before changing host-specific behavior.
The plugin root is the directory containing `.claude-plugin/plugin.json` or
`.codex-plugin/plugin.json`.

Shared instructions resolve the root through `$PLUGIN_ROOT` and name a server
plus the native Java tool, letting each host resolve its own prefixed spelling:
Claude Code and Codex get `mcp__minecraft-java__*`, Hermes Agent
`mcp__minecraft_java__*`. `${CLAUDE_PLUGIN_ROOT}` is Claude-only and the
validator rejects it outside the host table and the Claude agent definition.

Use logical model roles (`lead`, `specialist`, `executor`, and `host-default`)
in shared documentation. Claude frontmatter keeps its historical model values
for compatibility; Codex and Hermes use their configured model/reasoning setting
and native subagents or delegation where available, and run the phases
sequentially when they are not.

## Workflow invariants

- Keep the builder spine: survey → research → plan → blueprint/build →
  integrate → inspect → register → reflect, including the existing gates.
- Keep `minecraft-java` as the world MCP server and `minecraft-java-client` as
  the optional rendered-client inspection server. Keep tool names such as
  `server_get_status`, `view_capture`, `sense_*`, and `client_status` unchanged.
- Reuse the existing `build-*`, `survey-*`, `design-*`, `terrain-*`,
  `system-*`, `exec-*`, and `setup-*` skills. The entry skills are adapters,
  not replacements for those shared leaves.
- An absent rendered client never blocks a build: the report says
  **server-only inspection** instead of claiming a visual check.
- Preserve `.minecraft-builder/` as scratch state and the world registry as the
  durable build state. Never skip live verification when runtime access is
  unavailable; report the check as pending instead.

## Validation

Run these checks from the repository root:

```text
node scripts/validate-plugin.mjs
node --test scripts/tests/*.test.mjs
python <codex-install>/skills/.system/plugin-creator/scripts/validate_plugin.py .
python -m pytest tools/builder/tests tools/terrain/tests tools/voxel/tests
```

The Python plugin-validator path is specific to the local Codex installation;
the Node validator and its regression tests are the repository's
dependency-free CI checks. The Python suite needs
`python -m pip install -r tools/requirements.txt` and stays a manual gate.

The in-game evidence matrix lives in `docs/portability-smoke-test.md`; update it
when a live run happens rather than upgrading a static result to a live one.
