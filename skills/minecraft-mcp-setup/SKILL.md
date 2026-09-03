---
name: minecraft-mcp-setup
description: >-
  Set up the complete Minecraft Java Fabric MCP stack for Codex: prerequisites,
  Fabric and the MCP mod, server launch, MCP connection, and live status checks.
  Use when the Minecraft world server or optional rendered client is not ready.
---

# Minecraft MCP Setup for Codex

This is the Codex entrypoint for the existing four-phase setup agent. Reuse
`agents/minecraft-mcp-setup.md` for the detailed setup decisions and the shared
`setup-fabric`, `setup-mod`, `setup-server`, and `setup-connect` skills; this
file supplies only the host-specific connection adapter.

Read `reference/runtime-portability.md` and
`reference/mcp/codex-connection.md` before changing a local installation.

## Procedure

1. Check prerequisites and ask for the Minecraft directory, server/client
   topology, supported Minecraft version, and whether the installation is
   single-player or dedicated.
2. Run the existing setup phases in order, verifying each phase before moving
   on: `setup-fabric` → `setup-mod` → `setup-server` → `setup-connect`. When
   the shared `setup-connect` text presents a Claude CLI command, keep its
   endpoint and server-name semantics but use the Codex connection procedure
   below instead of executing that host-specific command.
3. Confirm the unchanged MCP names and tools. The world endpoint is
   `minecraft-java` and the optional rendered-client endpoint is
   `minecraft-java-client`; do not rename either one or translate Java tool
   names to a Bedrock surface.
4. Codex plugins provide the default local HTTP entries from
   `.codex-plugin/plugin.json`. For a remote or authenticated endpoint, use
   the commands in `reference/mcp/codex-connection.md` and keep the bearer
   token in an environment variable.
5. Verify with a live `server_get_status` call on `minecraft-java`. If a real
   client is running, also verify `client_status` and use `view_capture` when
   the workflow needs visual inspection. A server-only setup must be reported
   as server-only.

Do not claim setup is complete from file copies alone: the connection and the
actual server status must be checked. Invoke explicitly as
`$minecraft-java:minecraft-mcp-setup` when needed.
