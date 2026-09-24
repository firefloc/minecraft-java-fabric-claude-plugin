# Portability smoke test — Claude Code / Codex / Hermes Agent

Protocol and dated results for the Codex + Hermes port of the shared skill suite.
Every row below is **PASS**, **FAIL** or **NON TESTÉ** — a static validator run
never counts as an in-game result, and a probe MCP server is not Minecraft.

- Date: 2026-09-24
- Branch: `codex-hermes-portage`, based on `f18a71d`
- Machine: Linux, `fireflocpc`
- Hosts: Claude Code 2.1.280, Codex CLI 0.155.1, Hermes Agent v0.21.4
  (upstream `bba4d4f`)
- Minecraft: **not available on this machine** — no instance, and nothing
  listening on `127.0.0.1:8765` / `127.0.0.1:8766`

## Result summary

| Area | Claude Code | Codex | Hermes Agent |
| --- | --- | --- | --- |
| Static validation (validator + regression tests) | PASS | PASS | PASS |
| Plugin installs / loads from this checkout | PASS | PASS | PASS |
| All 30 skills discovered | PASS | PASS | PASS |
| Both MCP servers registered under the unchanged names | n/a (by design, see below) | PASS | PASS |
| MCP tool names discovered by the host | NON TESTÉ | NON TESTÉ | PASS (probe server) |
| Live session loads the two entry skills | NON TESTÉ | NON TESTÉ | NON TESTÉ |
| In-game build through the gated spine | NON TESTÉ | NON TESTÉ | NON TESTÉ |
| Server-only inspection reporting | NON TESTÉ | NON TESTÉ | NON TESTÉ |
| Rendered-client `client_status` + `view_capture` | NON TESTÉ | NON TESTÉ | NON TESTÉ |
| Remote/authenticated endpoint | NON TESTÉ | NON TESTÉ | NON TESTÉ |
| No secret in tracked files | PASS | PASS | PASS |

Nothing in the left-hand column is marked FAIL. The unverified rows need a
running Minecraft Java instance; the protocol to close them is at the bottom.

## Static validation

```sh
node scripts/validate-plugin.mjs      # manifests, skills, links, host portability
node --test scripts/tests/*.test.mjs  # regression tests for those checks
python -m pytest tools/builder/tests tools/terrain/tests tools/voxel/tests
python <codex-install>/skills/.system/plugin-creator/scripts/validate_plugin.py .
```

Results on this checkout:

- `node scripts/validate-plugin.mjs` → exit 0, "Claude and Codex plugin
  manifests, skills, and agents are valid".
- `node --test scripts/tests/*.test.mjs` → 5 pass / 0 fail. Each test breaks a
  throwaway copy of the repo (missing Hermes guide, hyphenated MCP prefix in a
  shared skill, `${CLAUDE_PLUGIN_ROOT}` in a shared skill, a missing skill from
  the 30) and asserts the validator fails on it.
- `python -m pytest …` → 136 passed in 3.4 s.
- Codex plugin validator → "Plugin validation passed".

The portability invariants now enforced automatically:

1. both connection guides exist (`reference/mcp/codex-connection.md`,
   `reference/mcp/hermes-connection.md`);
2. all 30 skills in the suite are present;
3. no shared instruction hardcodes the hyphenated `mcp__minecraft-java*` prefix
   (the host table and the Claude agent definition are exempt);
4. no shared instruction executes `${CLAUDE_PLUGIN_ROOT}` outside those two
   exempt files.

## Host surface

### Claude Code — PASS (component inventory)

```sh
claude --plugin-dir . plugin details minecraft-java
```

Reported: **Skills (30)**, Agents (4: the two shared agents plus the two Codex
adapters), Hooks (0), MCP servers (0), ~3,764 always-on tokens. The run loads
the plugin for the session only — nothing was installed into the user's Claude
configuration.

`MCP servers (0)` is expected, not a regression: the Claude surface registers
the MCP servers through `setup-connect` (`claude mcp add`), it does not ship a
`.mcp.json`, and `.mcp.json` is git-ignored so a per-user token can never land in
the repository.

### Codex — PASS (install + server registration)

Run against a throwaway `CODEX_HOME`, so the user's real Codex profile was not
touched:

```sh
CODEX_HOME=<scratch> codex plugin marketplace add .
CODEX_HOME=<scratch> codex plugin add minecraft-java@minecraft-java-claude
CODEX_HOME=<scratch> codex mcp list
```

- `plugin add` → "Added plugin `minecraft-java` … installed, enabled, 1.1.0".
- `codex mcp list` → both servers registered from the manifest:

  | Name | Url | Bearer Token Env Var | Status |
  | --- | --- | --- | --- |
  | `minecraft-java` | `http://127.0.0.1:8765/mcp` | – | enabled |
  | `minecraft-java-client` | `http://127.0.0.1:8766/mcp` | – | enabled |

- The installed package contains all 30 skill folders, both entry skills, the
  four agents and both connection guides.

Auth/status read `Unknown` because nothing is listening on those ports — the
correct reading with no Minecraft server running.

### Hermes Agent — PASS (discovery), PASS (tool naming, probe)

Skills, against a throwaway `HERMES_HOME` profile whose config points
`skills.external_dirs` at this checkout:

```sh
HERMES_HOME=<scratch> hermes skills list --source local
# → 0 hub-installed, 0 builtin, 30 local — 30 enabled, 0 disabled
```

Tool naming, against a local MCP probe that exposes the real Java tool names
(`server_get_status`, `level_get_info`, `view_capture`, `client_status`) on both
`minecraft-java` and `minecraft-java-client`:

```
mcp__minecraft_java__server_get_status
mcp__minecraft_java__level_get_info
mcp__minecraft_java_client__view_capture
mcp__minecraft_java_client__client_status
```

This confirms the documented normalization: Hermes rewrites every character
outside `[A-Za-z0-9_]`, so the hyphens in the server names become underscores.
The **probe is not Minecraft** — it proves the naming rule, not a world
connection.

A live Hermes session (`hermes -z`) was **NON TESTÉ**: the throwaway profile has
no provider credentials, and copying the user's credential store into a scratch
directory is not acceptable. Discovery was therefore verified by calling
Hermes's own `discover_mcp_tools()` in-process, which is the same code path a
session uses.

## In-game tests — NON TESTÉ

No Minecraft Java instance is available here, so every row below is untested
rather than passed. Run this protocol on a **throwaway test world** (never a
user's world):

| # | Test | Expected |
| --- | --- | --- |
| 1 | Load the two entry skills in each host; assert the 28 other skills are discoverable | entry skills fire, 30/30 discovered |
| 2 | `server_get_status`, then `level_get_info` (no writes) | version, TPS, players, dimensions |
| 3 | Same small reversible build requested from all three hosts | exactly one `build-*` orchestrator chosen, spine entered in order |
| 4 | Traces of the gates: survey, research, plan, blueprints/build, integrate, inspect, register, reflect | each phase entered; GATE B before inspect, GATE C before register |
| 5 | Server-only run | report says **server-only inspection**; no visual claim |
| 6 | Rendered client connected: `client_status`, then `view_capture` | the captured frame shows the built result |
| 7 | Remote endpoint with `MINECRAFT_MCP_URL` + a bearer token from the environment | identical endpoint in host and helper; no token in any log or tracked file |
| 8 | Cleanup | the test world is removed; no user world touched |

Record the Minecraft version actually used, without treating it as a product
decision — the port deliberately fixes no Minecraft version.

## Remote / authenticated endpoint

- Tracked files carry no token: `git log` for `bearer <value>`,
  `MINECRAFT_MCP_TOKEN=` assignments and similar finds only the unexpanded
  variable names and documentation placeholders in
  `reference/mcp/hermes-connection.md` and
  `reference/mcp/codex-connection.md`.
- `.mcp.json` (the local file that can hold a token) is git-ignored; only
  `.mcp.json.example` is tracked, and it reads the endpoint and token from the
  environment.
- Hermes, Codex and the bundled Python helpers all read the same variables
  (`MINECRAFT_MCP_URL`, `MINECRAFT_MCP_CLIENT_URL`, `MINECRAFT_MCP_TOKEN`,
  `MINECRAFT_MCP_CLIENT_TOKEN`), so one exported environment configures host and
  helpers identically.
- An actual call to a remote, authenticated Minecraft endpoint: **NON TESTÉ** —
  no endpoint available.

## Limits and remaining risk

1. **The in-game path is unverified.** Everything above is static or
   discovery-level. The port must not be described as "fully verified" until
   rows 1–8 of the in-game table have run.
2. **Visual verification is unverified.** Without a rendered client, no claim of
   visual inspection holds anywhere in this document.
3. **The Hermes prefix is a prediction validated against a probe.** The real
   mod's tool list is larger (the world server exposes ~10 categories of tools);
   the rule is the same, but the full list has not been observed over a live
   Minecraft connection.
4. **Codex and Claude live sessions are unverified.** Only plugin loading,
   registration and the component inventory were exercised.
5. **`$PLUGIN_ROOT`** must be resolved once per shell before running any shared
   example outside a host that expands `${CLAUDE_PLUGIN_ROOT}`. The shared docs
   say so in `reference/runtime-portability.md`; a reader who skips that line
   gets an empty variable.

## Protocol for the live run

1. Throwaway world: a dedicated test server or a copy of a world that can be
   destroyed.
2. `setup-fabric` → `setup-mod` → `setup-server` → `setup-connect` (the shared
   four-phase stack), verifying `server_get_status` after connection.
3. Run rows 1–8 above, one host at a time, recording the phase trail.
4. Fill this table in with real PASS/FAIL values and delete the "NON TESTÉ"
   language only for rows that actually ran.
