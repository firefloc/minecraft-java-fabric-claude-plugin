# Hermes Agent connection

Hermes Agent reads the shared `skills/` tree directly and talks to the same two
Streamable HTTP MCP servers as Claude Code and Codex. Nothing is copied: this
clone stays the single source of truth.

| Server | Default endpoint | Purpose |
| --- | --- | --- |
| `minecraft-java` | `http://127.0.0.1:8765/mcp` | World reads and writes (required) |
| `minecraft-java-client` | `http://127.0.0.1:8766/mcp` | Optional rendered-client inspection |

The client server is optional. A server-only or headless setup is a valid
configuration — the workflow then reports server-only inspection.

## 1. Expose the skills

Add an absolute path to this clone's `skills/` directory to the profile config
(`~/.hermes/config.yaml`, or `~/.hermes/profiles/<name>/config.yaml`). Quote or
escape the path if the checkout contains spaces:

```yaml
skills:
  external_dirs:
    - /absolute/path/to/the/clone/skills
mcp_servers:
  minecraft-java:
    url: http://127.0.0.1:8765/mcp
```

Add the inspection server in a second block, **only when a real rendered client
is running**:

```yaml
mcp_servers:
  minecraft-java-client:
    url: http://127.0.0.1:8766/mcp
```

Then verify discovery:

```sh
hermes skills list --source local
```

The success criterion is all 30 skills, not just the two entry skills
(`minecraft-builder`, `minecraft-mcp-setup`). A profile that shows fewer is a
path or precedence problem, not a partial install.

### Discovery rules worth knowing

- **Precedence.** A local skill (`~/.hermes/skills/`) and a trusted project
  skill both win over an `external_dirs` entry with the same name. A name
  collision means one of the 30 shared skills is silently shadowed — check for
  it rather than assuming the shared copy loaded.
- **Read-only is a convention, not a fence.** Hermes treats `external_dirs` as
  externally owned (creation goes to `~/.hermes/skills/`, name collisions are
  lost to local skills), but the files stay ordinary files on disk. Anyone with
  write access to the checkout can change the skills Hermes loads. Do not
  present `external_dirs` as a write protection.
- **`~` and `${VAR}` are expanded** in entries, relative paths resolve against
  `HERMES_HOME`, and a directory that does not exist is skipped quietly.

## 2. Tool names as Hermes sees them

Hermes normalizes every MCP server and tool name to `[A-Za-z0-9_]` and prefixes
it, so the hyphens in the server names become underscores:

| Shared name | Hermes name |
| --- | --- |
| `minecraft-java` + `server_get_status` | `mcp__minecraft_java__server_get_status` |
| `minecraft-java` + `level_get_info` | `mcp__minecraft_java__level_get_info` |
| `minecraft-java-client` + `view_capture` | `mcp__minecraft_java_client__view_capture` |
| `minecraft-java-client` + `client_status` | `mcp__minecraft_java_client__client_status` |

Shared instructions name the **server plus the native Java tool name** and let
Hermes resolve the prefixed form; do not write the prefixed spelling into a
shared skill. Confirm discovery with `hermes mcp test minecraft-java` and
`hermes mcp list`.

## 3. Remote or authenticated endpoint

Keep the token in the environment and out of the repository. Hermes reads
headers from the config, so reference the variable in the shell that starts
Hermes and interpolate it into the header value there — never commit the
expanded value:

```yaml
mcp_servers:
  minecraft-java:
    url: https://HOST:8765/mcp
    headers:
      Authorization: "Bearer ${MINECRAFT_MCP_TOKEN}"
```

```sh
export MINECRAFT_MCP_TOKEN=...   # supplied by whoever operates the endpoint
hermes mcp test minecraft-java
```

`MINECRAFT_MCP_URL` / `MINECRAFT_MCP_CLIENT_URL` and
`MINECRAFT_MCP_TOKEN` / `MINECRAFT_MCP_CLIENT_TOKEN` are the same variables the
bundled Python helpers read, so one shell environment configures the host and
the helpers consistently. Do not rename the server entries: the workflow and
every Java tool name depend on `minecraft-java` and `minecraft-java-client`.

## 4. Verify the connection

A configured server is not a connected one. Health checks and config presence
prove nothing — the minimum evidence is a live tool call:

1. Call `server_get_status` (no arguments). Minecraft version, TPS, online
   player count and loaded dimensions mean the chain works: Hermes → MCP server
   (the mod) → world.
2. Confirm world reads with `level_get_info` (`dimension: "minecraft:overworld"`).
3. **Only if a rendered client is connected:** call `client_status` (reports
   `in_game`, position, facing) and then `view_capture`. A returned frame is
   the only thing that proves visual inspection; without it, report the result
   as **server-only inspection**.

Failure modes: connection refused or timeout means the mod is not running;
a 401 means the token; tools that answer but error about no world or no player
mean a world is not loaded or nobody has joined.

## 5. Run the workflow

Once `server_get_status` answers, ask in plain language — "build a small
structure near the player" — and the `minecraft-builder` skill enters the
shared spine (survey → research → plan → blueprint/build → integrate → inspect →
register → reflect). `minecraft-mcp-setup` covers the four setup phases.
Delegation is optional: when no sub-agent facility is in use, the phases run
sequentially in one conversation and every gate still applies.
