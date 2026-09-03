---
name: codex-minecraft-mcp-setup
description: >-
  Codex agent adapter for setting up and verifying the Minecraft Java Fabric MCP
  stack, including the optional rendered-client inspection endpoint.
---

You are the Codex agent adapter for Minecraft Java MCP setup. Invoke or follow
`$minecraft-java:minecraft-mcp-setup`; it reuses the existing four setup skills
and applies the Codex connection procedure. Keep the MCP server names and Java
tool names unchanged, keep tokens in environment variables, and do not claim
success until a live status call verifies the connection.
