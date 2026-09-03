---
name: minecraft-builder
description: >-
  Lead the complete Minecraft Java build workflow in a live world. Use for any
  request to build, design, survey, inspect, improve, or verify a structure,
  settlement, landscape, terrain feature, or redstone system. Always preserve
  the gated survey, research, plan, blueprint/build, integrate, inspect,
  register, and reflect flow.
---

# Minecraft Builder for Codex

This is the Codex entrypoint for the existing `minecraft-builder` workflow. The
Claude Code agent at `agents/minecraft-builder.md` remains the detailed source
of truth; reuse its routing, state model, gates, and recovery rules instead of
copying them into a second implementation.

Before acting, read:

- `reference/runtime-portability.md` for path, model-role, and delegation rules.
- `reference/orchestration/workflow-spine.md` for the canonical phase order and
  gates.
- `agents/minecraft-builder.md` for the routing table and state/registry rules.

## Runtime adaptation

- Ignore Claude-only YAML metadata such as `model`, `effort`, `color`, and
  `context`. Use the current Codex model and reasoning setting. Map the source
  file's inline/fork intent to the current conversation or a native Codex
  subagent when one is available; if delegation is unavailable, run the same
  phase sequentially and keep every gate.
- Resolve references from the installed plugin root (the directory containing
  `.codex-plugin/plugin.json`) or from the repository checkout. Never pass a
  Claude-only path token literally to a shell.
- Use the MCP servers by their unchanged names: `minecraft-java` for world
  reads/writes and `minecraft-java-client` for optional rendered-player
  inspection. Use the existing Java tool names, including
  `server_get_status`, `view_capture`, `sense_*`, and `client_status`.

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
should enter this skill automatically. Users can also invoke it explicitly as
`$minecraft-java:minecraft-builder`.
