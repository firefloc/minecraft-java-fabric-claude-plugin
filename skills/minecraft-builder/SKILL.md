---
name: minecraft-builder
description: >-
  Lead the complete Minecraft Java build workflow in a live world. Use for any
  request to build, design, survey, inspect, improve, or verify a structure,
  settlement, landscape, terrain feature, or redstone system. Always preserve
  the gated survey, research, plan, blueprint/build, integrate, inspect,
  register, and reflect flow.
---

# Minecraft Builder — shared entrypoint (Claude Code, Codex, Hermes Agent)

This is the host-neutral entrypoint for the existing `minecraft-builder`
workflow. The Claude Code agent at `agents/minecraft-builder.md` remains the
detailed source of truth; reuse its routing, state model, gates, and recovery
rules instead of copying them into a second implementation.

Before acting, read:

- `reference/runtime-portability.md` for the host table, path, model-role, and
  delegation rules.
- `reference/orchestration/workflow-spine.md` for the canonical phase order and
  gates.
- `agents/minecraft-builder.md` for the routing table and state/registry rules.
- The connection guide for the host you are running on — `reference/mcp/codex-connection.md`
  under Codex; under Claude Code the plugin manifest already registers both
  servers. Every host's adapter is catalogued in the host table of
  `reference/runtime-portability.md`.

## Runtime adaptation

- Ignore host-specific YAML metadata such as `model`, `effort`, `color`, and
  `context`. Use the active host's configured model and reasoning setting. Map
  the source file's inline/fork intent to the current conversation or a native
  sub-agent when one is available; if delegation is unavailable, run the same
  phase sequentially and keep every gate.
- Resolve references from the installed plugin root (the directory containing
  `.claude-plugin/plugin.json` or `.codex-plugin/plugin.json`) or from the
  repository checkout, and quote the path. Never pass a Claude-only path token
  literally to a shell outside an explicitly Claude-labelled instruction.
- Use the MCP servers by their unchanged names: `minecraft-java` for world
  reads/writes and `minecraft-java-client` for optional rendered-player
  inspection. Use the existing Java tool names — `server_get_status`,
  `view_capture`, `sense_*`, `client_status` — and let the host resolve its own
  prefixed spelling (see the host table in `reference/runtime-portability.md`).
- When information the build genuinely needs is missing, ask one short question
  through the active interface. Never call a tool the active host does not
  provide by name.

## Required flow

1. Check `minecraft-java` with `server_get_status`. If it is unavailable, use
   `minecraft-mcp-setup` before attempting world writes.
2. Recover any matching project from the world registry and local scratch state.
3. Route to exactly one existing `build-*` orchestrator and follow the full
   spine: **survey → research → plan → shape/ecology → blueprint → build →
   integrate → inspect → register → reflect**. Research may be a no-op only
   for a genuinely imaginary request; the phase is still entered.
4. Keep the offline terrain gate before writes, the integrate gate before
   inspection, and the inspect/harness gate before registration.
5. Use the existing `exec-*`, `terrain-*`, `design-*`, and `system-*` skills as
   shared leaves. Do not invent a Codex-specific tool spelling or bypass the
   plan, blueprint, registry, or verification contracts.
6. When a rendered client is connected, use `minecraft-java-client` for the
   real-player frame and perception checks; otherwise report inspection as
   server-only rather than pretending a visual check happened.

Natural requests such as “build a lakeside village near the nearest player”
should enter this skill automatically. Explicit invocation is host-specific:
`$minecraft-java:minecraft-builder` under Codex, the `minecraft-builder` skill
name under Hermes Agent, and the builder agent under Claude Code.
