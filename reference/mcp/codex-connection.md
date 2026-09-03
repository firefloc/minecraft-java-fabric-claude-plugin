# Codex MCP connection

The Codex plugin manifest registers the same two Streamable HTTP MCP servers
used by the Claude integration:

| Server | Default endpoint | Purpose |
| --- | --- | --- |
| `minecraft-java` | `http://127.0.0.1:8765/mcp` | World reads and writes |
| `minecraft-java-client` | `http://127.0.0.1:8766/mcp` | Optional rendered-client inspection |

The client server is optional for a server-only or headless setup. In
single-player, one process may expose both endpoints.

## Local setup

Install the plugin, start the Fabric mod, and begin a new Codex conversation.
The plugin's `.codex-plugin/plugin.json` supplies the localhost entries. Verify
the connection with the unchanged `minecraft-java` tool `server_get_status`.
When a rendered client is running, verify `client_status` and use
`view_capture` for player-perspective inspection.

## Remote or authenticated setup

Keep the token out of the repository and configure the same server names in the
Codex MCP settings. The CLI form is:

```text
codex mcp add minecraft-java --url https://HOST:8765/mcp --bearer-token-env-var MINECRAFT_MCP_TOKEN
codex mcp add minecraft-java-client --url https://HOST:8766/mcp --bearer-token-env-var MINECRAFT_MCP_CLIENT_TOKEN
```

If a name is already configured, remove that existing entry before adding the
replacement. Set the referenced environment variable in the shell that starts
Codex. Do not rename the entries: the workflow and all existing Java tool names
depend on `minecraft-java` and `minecraft-java-client`.

The bundled helper scripts additionally accept `MINECRAFT_MCP_URL` and
`MINECRAFT_MCP_CLIENT_URL` for endpoint-only overrides, and read bearer tokens
from `MINECRAFT_MCP_TOKEN` / `MINECRAFT_MCP_CLIENT_TOKEN`.
