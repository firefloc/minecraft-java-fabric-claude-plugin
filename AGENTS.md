# AGENTS.md

This repository ships one Minecraft Java workflow with two host adapters:

- Claude Code: `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`,
  `CLAUDE.md`, and the existing `agents/*.md` files.
- Codex: `.codex-plugin/plugin.json`, `agents/openai.yaml`, the two compact
  agent adapters under `agents/codex-*.md`, and the two thin entry skills
  `minecraft-builder` and `minecraft-mcp-setup`.

The `skills/` tree, `reference/` tree, `tools/` tree, MCP server names, and Java
tool names are shared. Keep the Claude surface intact when changing the Codex
adapter; do not fork the builder logic just to change host syntax.

## Runtime rules

Read `reference/runtime-portability.md` before changing host-specific behavior.
The plugin root is the directory containing `.codex-plugin/plugin.json` or
`.claude-plugin/plugin.json`. Claude-only path tokens may remain in legacy
Claude instructions, but Codex instructions must resolve paths from the actual
plugin root and must never execute a literal token.

Use logical model roles (`lead`, `specialist`, `executor`, and `host-default`)
in shared documentation. Claude frontmatter keeps its historical model values
for compatibility; Codex uses the configured model/reasoning setting and native
subagents where available.

## Workflow invariants

- Keep the builder spine: survey → research → plan → blueprint/build →
  integrate → inspect → register → reflect, including the existing gates.
- Keep `minecraft-java` as the world MCP server and `minecraft-java-client` as
  the optional rendered-client inspection server. Keep tool names such as
  `server_get_status`, `view_capture`, `sense_*`, and `client_status` unchanged.
- Reuse the existing `build-*`, `survey-*`, `design-*`, `terrain-*`,
  `system-*`, `exec-*`, and `setup-*` skills. The Codex wrappers are adapters,
  not replacements for those shared leaves.
- Preserve `.minecraft-builder/` as scratch state and the world registry as the
  durable build state. Never skip live verification when runtime access is
  unavailable; report the check as pending instead.

## Validation

Run these checks from the repository root:

```text
node scripts/validate-plugin.mjs
python <codex-install>/skills/.system/plugin-creator/scripts/validate_plugin.py .
python -m pytest tools/builder/tests tools/terrain/tests tools/voxel/tests
```

The Python plugin-validator path is specific to the local Codex installation;
the Node validator is the repository's dependency-free CI check.
