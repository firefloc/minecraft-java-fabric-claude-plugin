# Portability smoke test — Claude Code / Codex / Hermes Agent

Protocol and dated results for the Codex + Hermes port of the shared skill suite.
Every row below is **PASS**, **FAIL** or **NON TESTÉ** — a static validator run
never counts as an in-game result, and a probe MCP server is not Minecraft.

- Date: 2026-09-24
- Branch: `codex-hermes-portage`, based on `f18a71d`
- Machine: Linux, `fireflocpc`
- Hosts: Claude Code 2.1.280, Codex CLI 0.155.1, Hermes Agent v0.21.4
  (upstream `bba4d4f`)
- Minecraft: **a throwaway dedicated test server is available** — see
  *Test server install* below. Version Minecraft 1.21.11 / Fabric loader 0.19.5 /
  `minecraft-fabric-mcp` 1.1.0, 104 tools. This is the version the live rows ran
  on, not a version the port chooses or supports exclusively.
- Rendered client: **none** — no Minecraft client instance exists on this
  machine, so every visual row stays NON TESTÉ.

## Result summary

| Area | Claude Code | Codex | Hermes Agent |
| --- | --- | --- | --- |
| Static validation (validator + regression tests) | PASS | PASS | PASS |
| Plugin installs / loads from this checkout | PASS | PASS | PASS |
| All 30 skills discovered | PASS | PASS | PASS |
| Both MCP servers registered under the unchanged names | n/a (by design, see below) | PASS | PASS |
| MCP tool names discovered by the host | NON TESTÉ | NON TESTÉ | PASS (live server + probe) |
| Live session loads the two entry skills | NON TESTÉ | NON TESTÉ | PASS |
| In-game build through the gated spine | NON TESTÉ | NON TESTÉ | PASS |
| Server-only inspection reporting | NON TESTÉ | NON TESTÉ | PASS |
| Rendered-client `client_status` + `view_capture` | NON TESTÉ | NON TESTÉ | NON TESTÉ |
| Remote/authenticated endpoint | NON TESTÉ | NON TESTÉ | NON TESTÉ |
| No secret in tracked files | PASS | PASS | PASS |

Nothing in the table is marked FAIL. Hermes Agent is verified end to end against
a real Minecraft server; Claude Code and Codex are verified up to plugin loading
and component inventory, and their live sessions were not exercised.

The script that produces the Hermes column is in the repository:

```sh
python3 scripts/hermes-smoke.py        # static + live, SKIPs what is absent
HERMES_HOME=<profile> python3 scripts/hermes-smoke.py
```

## Test server install

Installed with the shared `setup-*` procedure itself, on a scratch directory
(`~/.hermes/cache/scratch/mc-test-server`), never in the user's Minecraft or
server installs:

| Step | Command / artefact |
| --- | --- |
| Fabric installer | `fabric-installer` from `maven.fabricmc.net`, `server -mcversion 1.21.11` |
| Loader | resolved from `meta.fabricmc.net/v2/versions/loader/1.21.11` |
| Fabric API | `fabric-api-0.141.6+1.21.11.jar` (Modrinth) |
| MCP mod | `minecraft-fabric-mcp-1.1.0+1.21.11.jar` (GitHub release) |
| Config | `config/minecraft_fabric_mcp/config.json` → `127.0.0.1:8765`, `auth_required: false` |
| World | `testworld`, superflat-free default generation, creative, throwaway |

Boot evidence, straight from the server log:

```
MCP server config loaded from ./config/minecraft_fabric_mcp/config.json
MCP server pre-start complete: 104 tools registered, listening on http://127.0.0.1:8765
MCP server listening at http://127.0.0.1:8765 (host=127.0.0.1, port=8765, auth=false, tls=false)
Done (1.662s)! For help, type "help"
```

`curl http://127.0.0.1:8765/healthz` → `{"status":"ok"}`. The documented
procedure works verbatim; the only number off is the tool count ("about 103
tools" in `setup-server`), now 104 with this mod build.

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
- `node --test scripts/tests/*.test.mjs` → 8 pass / 0 fail. Each negative test
  breaks a throwaway copy of the repo (missing Hermes guide, hyphenated MCP
  prefix in a shared skill, `${CLAUDE_PLUGIN_ROOT}` in a shared skill, a missing
  skill from the 30) and asserts the validator fails on it; three more check the
  Hermes guide against the code it describes (prefix table vs Hermes's
  normalization rule, the config keys, the entry skills it promises).
- `python3 scripts/hermes-smoke.py` → 9 passed, 0 failed, 2 info (live server).
- `python -m pytest …` → 136 passed in 3.4 s.
- Codex plugin validator → "Plugin validation passed".
- `git diff --check` → clean; `git status --short` shows only the delivery docs
  modified.

The portability invariants now enforced automatically:

1. both connection guides exist (`reference/mcp/codex-connection.md`,
   `reference/mcp/hermes-connection.md`);
2. all 30 skills in the suite are present;
3. no shared instruction hardcodes the hyphenated `mcp__minecraft-java*` prefix
   (the host table and the Claude agent definition are exempt);
4. no shared instruction executes `${CLAUDE_PLUGIN_ROOT}` outside those two
   exempt files;
5. the Hermes guide's server/tool→prefixed-name table matches the normalization
   rule Hermes actually applies, and the entry skills it names exist.

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

A live Hermes session was **run** (`hermes -z` against a throwaway `HERMES_HOME`
whose `skills.external_dirs` points at this checkout, with the world server
registered). Asked to name what it saw, it answered:

```
1) 30 skills.
2) mcp__minecraft_java__server_get_status
3) mcp__minecraft_java__level_get_info
```

That is the documented prefix, produced by a real session rather than predicted
from a probe.

`scripts/hermes-smoke.py` against the same live server:

```
PASS  30-skill suite on disk — 30 skills
PASS  entry skill minecraft-builder
PASS  entry skill minecraft-mcp-setup
PASS  guide prefix table matches Hermes normalization — 4 rows, 0 wrong
PASS  Hermes CLI discovery — 30/30 skills visible
PASS  live MCP handshake — minecraft-java-fabric-mcp-server 1.1.0
PASS  tools/list — 104 tools
PASS  call server_get_status — minecraftVersion: 1.21.11 …
PASS  call level_get_info — dimensionId: "minecraft:overworld" …
INFO  rendered-client tool client_status — absent — the workflow must report server-only inspection
INFO  rendered-client tool view_capture — absent — the workflow must report server-only inspection

9 passed, 0 failed, 2 skipped/info
```

### Hermes Agent — PASS (in-game build)

The same session was then asked to load `minecraft-builder` and run a small
reversible build against the live server (a full 3×3×3 `minecraft:stone` cube at
`(10,90,10)`–`(12,92,12)`, nothing else touched). Verbatim from its report:

- `server_get_status` → Minecraft 1.21.11, Fabric 0.19.5, mod 1.1.0, 104 tools,
  TPS 20, overworld loaded.
- A **pre-write scan** showed the 27 target blocks were air, so the write
  overwrote nothing — the workflow's non-destructive discipline held.
- `block_fill_region` on `(10,90,10)`→`(12,92,12)`, mode `replace`,
  `minecraft:stone` → "filled 27 block(s)".
- Post-write `block_get_state` on three corners/centre → `minecraft:stone`;
  `block_scan_summary` → 27/27 non-air, histogram `{minecraft:stone: 27}`, bounds
  exactly the requested box; a 5×5×5 control scan confirmed nothing outside the
  cube changed.

Its own verdict lines:

```
PORTES: SURVEY → RESEARCH (vide) → PLAN (dans la requête) → BUILD → INSPECT ;
        REGISTER entrée mais non écrite, REFLECT vide, GATE B sans objet
INSPECTION: server-only
OUTILS: mcp__minecraft_java__server_get_status, mcp__minecraft_java__level_get_info,
        mcp__minecraft_java__block_scan_summary, mcp__minecraft_java__block_fill_region,
        mcp__minecraft_java__block_get_state, mcp__minecraft_java__data_storage_get
```

The gate trail is honest rather than decorative: RESEARCH was entered and left
empty (no real reference for a test cube), GATE B is genuinely inapplicable
(free air, no terrain integration), and REGISTER stayed read-only because the
request forbade writes outside the cube.

Independently re-checked over MCP after the run, then reverted:

```
centre    : id: "minecraft:stone" … position: x: 11 y: 91 z: 11
boite     : scanned_volume: 27  non_air: 27  bounds (10,90,10)-(12,92,12)  {minecraft:stone: 27}
revert    : filled 27 block(s)
apres     : scanned_volume: 27  non_air: 0
```

The test world is back to its pre-test state.

## In-game tests — Hermes PASS, Claude/Codex NON TESTÉ

Run on the throwaway test server above. Rows 1–5 and 8 ran on **Hermes Agent**;
Claude Code and Codex rows are untested because their live sessions were not
exercised (see *Limits*). Row 6 needs a rendered client, which does not exist
here; row 7 needs a remote endpoint.

| # | Test | Hermes Agent | Claude Code | Codex |
| --- | --- | --- | --- | --- |
| 1 | Entry skills fire; the 28 other skills stay discoverable | PASS — 30 skills, both entry skills, `minecraft-builder` drove the build | NON TESTÉ | NON TESTÉ |
| 2 | `server_get_status`, then `level_get_info` (no writes) | PASS — 1.21.11, 104 tools, TPS 20; overworld, spawn, difficulty | NON TESTÉ | NON TESTÉ |
| 3 | Same small reversible build on all three hosts | PASS (Hermes): one fill of the exact requested box; no orchestrator thrash | NON TESTÉ | NON TESTÉ |
| 4 | Gate trail: survey, research, plan, build, integrate, inspect, register, reflect | PASS — trail reported with GATE B correctly inapplicable and REGISTER left read-only | NON TESTÉ | NON TESTÉ |
| 5 | Server-only run | PASS — `INSPECTION: server-only`, no visual claim made | NON TESTÉ | NON TESTÉ |
| 6 | Rendered client: `client_status`, then `view_capture` | NON TESTÉ — no client instance; both tools absent from the world server | NON TESTÉ | NON TESTÉ |
| 7 | Remote endpoint with `MINECRAFT_MCP_URL` + token from the environment | NON TESTÉ — no remote endpoint available | NON TESTÉ | NON TESTÉ |
| 8 | Cleanup | PASS — the cube was reverted (27/27 non-air → 0); the world is throwaway | NON TESTÉ | NON TESTÉ |

The Minecraft version actually used is recorded above (1.21.11) as a test
detail; the port deliberately fixes no Minecraft version.

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

## Spec traceability

Every requirement of
`docs/superpowers/specs/2026-09-24-codex-hermes-portage-design.md`, the change
that carries it, and the control that proves it:

| Spec requirement | Change | Control |
| --- | --- | --- |
| One 30-skill suite drives the same server from three hosts | shared `skills/`, `reference/`, `tools/`; per-host adapters only | validator's 30-skill list; `claude plugin details`; `hermes skills list`; Codex package contents |
| Same spine on each host, gates included | entry skills made host-neutral; spine untouched | `rg -n 'survey\|research\|plan\|inspect\|register\|reflect'` on the entry skill + spine; `workflow-spine.md` unchanged |
| `server_get_status` is the minimum connection proof; `view_capture` proves visual | `setup-connect` shared verification section | smoke matrix rows 2 and 5 PASS on Hermes against a live server; row 6 NON TESTÉ |
| Absent rendered client → "server-only inspection" | `exec-inspect` graceful-degradation text; `setup-connect` wrap-up; AGENTS.md invariant | wording in both skills + the smoke matrix |
| No token in Git, stdout or a shared command | environment variables in both guides; `.mcp.json` git-ignored | `git grep` for bearer values and token assignments |
| Decision 1 — shared trunk, no per-host copy | no new `skills/` tree; Hermes reads this checkout | validator 30-skill list + `hermes skills list` |
| Decision 2 — `skills.external_dirs` | `reference/mcp/hermes-connection.md`; README | 30/30 discovery on a throwaway `HERMES_HOME` |
| Decision 3 — invariant server/tool names, host-resolved prefix | host table in `runtime-portability.md`; T4 rewrites | validator check: no hyphenated prefix in shared instructions; probe discovery of both prefixes |
| Decision 4 — plugin-root resolution, no cwd assumption, quoted paths | `$PLUGIN_ROOT` across the corpus | path-with-spaces run from outside the checkout |
| Decision 5 — Claude metadata kept, logical roles elsewhere, sequential without sub-agents | host table + entry skills | no Claude metadata removed; validator's Codex/Claude metadata rules |
| Decision 6 — env vars as the common MCP parameter source, no YAML parser | guides + unchanged `tools/mcp_config.py` | `tools/builder/tests/test_mcp_config.py` (136 tests pass) |
| Discovery contract — entry skills + the 28 others reachable; name conflict detectable | Hermes guide's precedence section | 30/30 discovery; precedence documented |
| User interaction — no literal `AskUserQuestion` on a host that lacks it | T4 rewrites across nine files | `rg AskUserQuestion` → host table only |
| Inspection — host discovers tool names; visual needs a real client | T4 rewrites in `exec-inspect` and `engine-limits` | validator check; smoke matrix (NON TESTÉ) |
| Out of scope: no Minecraft version chosen, no Fabric rewrite, no user-profile install | only docs/skills/scripts touched; throwaway `HERMES_HOME` / `CODEX_HOME` | `git diff --stat`; real Hermes install and `~/.codex/config.toml` verified untouched |

## First request, and what to do when it fails

The same request works on every host — no host-specific phrasing:

> Build a small stone-brick house near the nearest player.

What should happen, in order:

1. The builder entry skill fires and routes to exactly one `build-*`
   orchestrator (`build-structure` for that request).
2. `server_get_status` answers on the `minecraft-java` server.
3. The spine runs gated: survey → research → plan → blueprint/build →
   integrate (GATE B) → inspect (GATE C) → register → reflect.
4. With no rendered client, the report says **server-only inspection**.

Diagnosis when `server_get_status` fails:

| Symptom | Cause | Fix |
| --- | --- | --- |
| connection refused / timeout | the mod is not running, or wrong host:port | start Minecraft with the mod (or the dedicated server); confirm `/healthz` answers on the same host and port |
| 401 on tool calls but `/healthz` is fine | bearer token missing, wrong, or has a stray space | export `MINECRAFT_MCP_TOKEN` in the shell that starts the host |
| the tool is not found at all | server name changed, or the host never registered it | re-run `setup-connect` for that host; confirm with `claude mcp list`, `codex mcp list` or `hermes mcp list` |
| tools answer but complain about no world / no player | nothing is loaded | load a world and have a player join, then retry |
| Hermes finds 0 or few skills | `skills.external_dirs` points at the wrong directory, or a local skill shadows a shared one | `hermes skills list --source local`; expect all 30 |

If the world server cannot be reached at all, the work stops there: report the
attempt as pending rather than substituting a static check for a live one.

## Limits and remaining risk

1. **Claude Code and Codex live sessions are unverified.** Only plugin loading,
   registration and the component inventory were exercised. The Hermes column is
   the only end-to-end one, so a Claude- or Codex-specific failure in the spine
   would not have been caught here.
2. **Visual verification is unverified.** No rendered client exists on this
   machine, so no claim of visual inspection holds anywhere in this document.
   `client_status` and `view_capture` were never called against a real client.
3. **One build shape, one world, one mod build.** The live run covered a single
   box fill in the overworld. Terrain, nether/end dimensions, structures with
   datapacks, and the client-server code paths are untouched by it.
4. **The in-game rows that could not run are still NON TESTÉ**, not "fine": the
   rendered-client row (6) and the remote/token row (7).
5. **`$PLUGIN_ROOT`** must be resolved once per shell before running any shared
   example outside a host that expands `${CLAUDE_PLUGIN_ROOT}`. The shared docs
   say so in `reference/runtime-portability.md`; a reader who skips that line
   gets an empty variable.
6. **Pre-existing, out of portage scope:** `player_list_online` is invoked in
   `skills/survey-site/SKILL.md` and `skills/exec-worker/SKILL.md`, but the live
   world server exposes **no `player_*` tool at all** (the player-adjacent
   families are `entity_*`, and player presence shows up in
   `server_get_status.onlinePlayerCount`). The port did not introduce or fix
   this — it is a doc/mod drift the live run happened to expose, and it is worth
   its own issue: either the name is wrong, or a mod build must supply it.
7. **`setup-server` says "about 103 tools"; this mod build registers 104.** The
   wording is approximate so it does not fail, but the number is not a contract.
8. **The test server is still running** on `127.0.0.1:8765` in a scratch
   directory. Stop it before doing anything heavy on this machine, and delete
   `~/.hermes/cache/scratch/mc-test-server` when it is no longer needed.

## Protocol for re-running on another host

The Hermes column was produced this way; reuse it for Claude Code and Codex.

1. Throwaway world: a dedicated test server (or a copy of a world that can be
   destroyed). The scratch install above is one; `setup-fabric` → `setup-mod` →
   `setup-server` → `setup-connect` is the shared four-phase stack that built it.
2. Register the `minecraft-java` server for the host under test, then verify the
   connection with `server_get_status` (never with a health check alone).
3. Run rows 1–8 above, one host at a time, recording the phase trail and the
   exact prefix the host resolves for each tool.
4. Revert whatever the build wrote, then update the table with real PASS/FAIL
   values — keep NON TESTÉ only for rows that genuinely did not run.
5. `python3 scripts/hermes-smoke.py` reproduces the Hermes column's static and
   live checks in one command; for the other hosts, `claude plugin details`,
   `codex mcp list` and the component inventory are the equivalents.
