<p align="center">
  <img src="docs/images/logo.png" width="200" alt="Minecraft Java Fabric MCP — Claude plugin logo">
</p>

# Minecraft Java — Claude Code + Codex Plugin

A shared [Claude Code](https://code.claude.com) and [OpenAI Codex](https://openai.com/codex/)
plugin that gives an agent **skills** and a **builder workflow** for driving a
live Minecraft Java Edition world through the
[`minecraft-java-fabric-mcp-server`](https://github.com/chapmanjw/minecraft-java-fabric-mcp-server)
— a Fabric mod that embeds an MCP server inside Minecraft.

![A voxel mascot standing on a superflat world, built by the minecraft-builder agent](docs/images/bean.png)

*Built by the `minecraft-builder` agent: authored as a parametric voxel model,
render-checked against the design before placing, stamped into the world in a
single batch, then verified in-world — block-for-block.*

![Ghasticlawd, a voxel Ghast-and-Claude mascot, built in a live world](docs/images/ghasticlawd.png)

*And **Ghasticlawd** — the project's Ghast × Claude mascot — built the same way:
voxelized, render-verified against the design, then placed and confirmed in-world.*

![A layered red-rock canyon inspired by the national parks of the American West, terraformed in a live world](docs/images/canyon.png)

*And terrain, not just figures — this red-rock canyon, inspired by the national
parks of the American West, was shaped by the `terrain-shape` skill's terrain
toolkit: a parametric heightfield, hydraulically eroded, render-checked against
the design, then materialized into the world as block fills.*

It does two things:

1. **Guided setup** — skills and an agent that walk you, step by step, through
   standing up the whole stack: Minecraft Java with the Fabric loader, the MCP
   mod and its Fabric API dependency, the mod's configuration, and the
   connection to Claude Code or Codex.
2. **Building in the world** — a `minecraft-builder` agent that routes each
   request to one of four `build-*` orchestrators, each of which sequences a set
   of model-tuned leaf skills — survey, research, plan, blueprint, build, verify,
   reflect — to design and construct elements in a live world.

## The stack

This plugin is the agent-facing piece of a two-repository system. It supports
both Claude Code and Codex; the MCP server is **embedded in the Fabric mod** and
runs inside Minecraft itself — there is no separate server process and no
behavior pack.

| Repository | Role |
| ---------- | ---- |
| [`minecraft-java-fabric-mcp-server`](https://github.com/chapmanjw/minecraft-java-fabric-mcp-server) | The Fabric mod. Embeds the MCP HTTP server and executes tool calls against the world on the server main thread. |
| **`minecraft-java-fabric-claude-plugin`** (this repo) | The Claude Code + Codex plugin — shared skills, host adapters, and agents that use the MCP tools. |

```
Claude Code / Codex
   │  MCP over Streamable HTTP  (http://127.0.0.1:8765/mcp)
minecraft-java-fabric-mcp-server   ← Fabric mod; embeds the MCP server
   │  Minecraft server API + Fabric API  (on the main thread)
the Minecraft world
```

## ⚠️ Pin your versions

The mod ships a separate jar for each supported Minecraft version, built against
that version's Fabric API. A Minecraft or Fabric update can change the modding
surface the mod depends on. Pin your Minecraft version, your Fabric API jar, and
the mod jar to a matched, known-good set and upgrade them together. The mod's
release notes list the supported Minecraft versions (currently **1.21.11, 26.1.1,
26.1.2, and 26.2**). Each jar is pinned to its exact Minecraft version, so a jar
built for one will refuse to load on another. Treat the whole stack as experimental.

Get the MCP server mod from
[**Modrinth**](https://modrinth.com/mod/fabric-api-mcp-server) or
[**CurseForge**](https://www.curseforge.com/minecraft/mc-mods/fabric-api-mcp-server)
(or the [GitHub Releases page](https://github.com/chapmanjw/minecraft-java-fabric-mcp-server/releases)) —
pick the jar matching your Minecraft version. The `setup-mod` skill walks you through it.

## Install with Claude Code

Add this repo as a plugin marketplace and install the plugin:

```
/plugin marketplace add chapmanjw/minecraft-java-fabric-claude-plugin
/plugin install minecraft-java@minecraft-java-claude
```

Then restart Claude Code. The skills appear under `/minecraft-java:*` and the
`minecraft-mcp-setup` and `minecraft-builder` agents become available for
delegation.

## Install with Codex

This repository includes the Codex manifest at
[`.codex-plugin/plugin.json`](.codex-plugin/plugin.json), Codex UI metadata at
[`agents/openai.yaml`](agents/openai.yaml), and two Codex entry skills. The
existing `skills/`, `reference/`, `tools/`, and MCP tool surface are shared with
Claude Code; no second builder implementation is installed.

Codex plugin discovery is marketplace-based. This repository is the plugin root
(rather than a marketplace containing a `plugins/` directory), so the portable
local setup is to place it under `~/plugins/minecraft-java` and add one entry to
your personal marketplace. Clone it there, or use a junction/symlink to an
existing checkout:

```text
~/plugins/minecraft-java/.codex-plugin/plugin.json
~/.agents/plugins/marketplace.json
```

Add this object to the existing `plugins` array in
`~/.agents/plugins/marketplace.json` (create the file using the surrounding
marketplace format if it does not exist):

```json
{
  "name": "minecraft-java",
  "source": { "source": "local", "path": "./plugins/minecraft-java" },
  "policy": { "installation": "AVAILABLE", "authentication": "ON_INSTALL" },
  "category": "Games"
}
```

Restart Codex, then install `minecraft-java` from the marketplace name shown in
that file:

```sh
codex plugin add minecraft-java@<marketplace-name>
```

If the repository is already published in a Codex marketplace, install it from
that marketplace instead. Start a new Codex conversation after installation so
the new skills and MCP entries are loaded.

Codex can invoke the entrypoints naturally from requests such as “build a
lakeside village near the nearest player”, or explicitly:

```text
$minecraft-java:minecraft-builder
$minecraft-java:minecraft-mcp-setup
```

The first entrypoint preserves the complete
**survey → research → plan → blueprint/build → integrate → inspect → register →
reflect** workflow. The second runs the existing four setup phases in order.

## Setup skills

The four setup skills are meant to be run **in order**. Each one ends by
handing off to the next. The default path is a **single-player** install on
localhost (no token, no firewall changes); each skill also covers the
**dedicated Fabric server** branch (LAN/remote, bearer-token auth).

| Skill | Phase | What it covers |
| ----- | ----- | -------------- |
| `setup-fabric` | 1 | Install Minecraft Java Edition and the Fabric loader — a single-player client or a headless dedicated server. |
| `setup-mod` | 2 | Download the MCP mod jar and the matching Fabric API jar and install both into the `mods/` folder. |
| `setup-server` | 3 | Configure the mod's `config.json`, launch, and verify the embedded MCP server is listening (`/healthz`); capture the bearer token for remote setups. |
| `setup-connect` | 4 | Register the MCP server with Claude Code or Codex and verify with a live tool call. |

To start a fresh setup, ask Claude Code or Codex to set up Minecraft Java for
MCP — the host adapter triggers automatically — or invoke the shared setup skill
explicitly in Claude Code:

```
/minecraft-java:setup-fabric
```

## Builder skills

The build pipeline is organized in three tiers. The `minecraft-builder` agent is
Tier 1: it owns state and the quality gates and routes every request to exactly
one Tier-2 orchestrator. The four `build-*` orchestrators are domain playbooks
that sequence the Tier-3 leaf skills and thread one shared coherence context (one
survey, one terrain recipe, one palette, one biome plan, one integration pass) so
a build holds together. The leaves are single-purpose specialists, assigned by
logical role: `lead`, `specialist`, or `executor`. Claude retains its historical
model metadata for compatibility; Codex uses the configured model and native
subagents when available. A leaf never hands off to a sibling; it returns its
result to the orchestrator, which sequences the next leaf. There is no trivial
path: every request runs the full gated spine, depth-scaled. The repository now
contains the original shared skills plus two host entry skills.
You can invoke any one directly, but the agent is the intended entry point.

The full list, tiers, and runtime-role mapping live in
[`skills/TAXONOMY.md`](skills/TAXONOMY.md).

**Tier 2 — `build-*` orchestrators** (`lead`, inline). Every request maps to one:

| Skill | Routes for |
| ----- | ---------- |
| `build-natural-world` | terrain, landforms, biomes, water, natural scenery, named natural wonders, caves |
| `build-settlement` | villages, cities, districts, a building with grounds and context |
| `build-structure` | one named or standalone building, replica, statue/monument, player house |
| `build-systems` | redstone, farms, contraptions, transit lines, nether hubs, mechanisms |

**Tier 3 — leaf specialists**, grouped by prefix:

| Skill | Role | Runtime role |
| ----- | ---- | ----- |
| `survey-site` | Investigates the live world — terrain, biomes, existing builds, surroundings. | specialist |
| `survey-research` | Researches real-world references, including geology and ecology, for faithful recreation. | specialist |
| `terrain-shape` | Designs naturalistic terrain as a recipe — mountains, water, biomes. | specialist |
| `terrain-landmark` | Composes recognizable real-world natural wonders from formation primitives. | specialist |
| `terrain-ecology` | Plants biome ecology and runs the scatter recipe. | specialist |
| `terrain-integrate` | Grounds a build into the world — apron erosion, seam blend (Gate B). | specialist |
| `terrain-cave` | Designs subterranean space — caves, caverns, ravines. | specialist |
| `design-house` | Designs a player's base of operations. | lead |
| `design-village` | Designs settlements up to ~15 buildings, reusing standard building types. | lead |
| `design-city` | Designs cities and districts (~16+) — urban fabric, zoning, streets, vernacular reuse. | lead |
| `design-building` | Designs specific named buildings — real-world and fictional replicas, originals. | lead |
| `design-monument` | Designs monuments and build-art — statues, creatures, sculpture, pixel art, logos. | lead |
| `design-grounds` | Designs intentional outdoor space — gardens, parks, plazas, courtyards, hedge mazes. | lead |
| `system-redstone` | Designs and verifies redstone and mechanical contraptions — Java-correct, with functional tests. | lead |
| `system-transit` | Designs the connective network between builds — rail, roads, nether hubs, bridges, tunnels. | lead |
| `exec-plan` | Captures requirements, interviews the user, produces a fully-resolved `plan.toon`. | lead |
| `exec-blueprint` | Turns the plan into named, reusable `mcb:*` structure templates in the world. | specialist |
| `exec-worker` | Executes the plan step by step via the harness — mechanical, no redesign. | executor |
| `exec-inspect` | Verifies each build phase in-world and proposes course corrections (Gate C). | specialist |
| `exec-reflect` | Reviews the finished job and drafts process lessons for project memory. | specialist |

The `terrain-*`, `design-*`, `system-*`, and `exec-*` leaves carry `reference/`
libraries loaded on demand so the detail never bloats context until it is needed —
landforms and command budgets, rooms and styles and layouts, village mechanics,
urban zoning, architectural technique, redstone limits, contract checks, blueprint
rendering. The shared terrain core (`reference/terrain/` — palettes, water,
weathering, formation primitives, non-negotiables) is promoted to the plugin root
and linked by every terrain leaf rather than copied.

For representational and parametric builds (vehicles, creatures, statues),
`design-monument` runs a **render-verify loop** backed by a bundled Python voxel
toolkit (`tools/voxel/`, numpy + Pillow): author the form as a parametric model,
render three orthogonal views to PNG and check the silhouette *before* placing a
block, stamp the whole thing into the world in one `block_fill_batch`, then confirm
with an in-world `block_render_region`. See [`tools/README.md`](tools/README.md).
The agent can't see the world, and a wrong silhouette can't be detailed away — so
the cheap iteration happens on a render first. (The bean above was built exactly
this way.)

Terrain works the same way through a separate toolkit. `terrain-shape` and the
other terrain leaves author land as a **recipe** — a composable sampler graph —
verify it offline (Gate A: ziggurat, seam, and relief checks), and materialize it
with `block_fill_columns` in one server call rather than a voxel grid. The terrain
toolkit (`tools/terrain/`) adds **scipy** to the numpy + Pillow base, and uses
**opensimplex** when present (falling back to Perlin noise otherwise). The build
harness (`tools/builder/`) is stdlib-only. Install all the Python deps once with
`python -m pip install -r tools/requirements.txt`.

## Agents

**`minecraft-mcp-setup`** — orchestrates the complete setup end to end. It runs
all four phases in one continuous session: checks prerequisites up front, works
each phase interactively, verifies every phase's checklist before advancing,
and carries forward the values later phases depend on (paths, ports, token,
host).

**`minecraft-builder`** — designs and constructs elements in a live world. It
health-checks the MCP connection (and points you at `minecraft-mcp-setup` if
the world isn't reachable), recovers existing project state from the world, then
routes the request to one of the four `build-*` orchestrators, which sequences the
leaf skills through one gated spine: survey → research → plan → shape → ecology →
blueprint → build → integrate → inspect → register → reflect. Delegate to it for
any build — e.g. *"Build a lakeside village near the nearest player."*

Use the individual `/minecraft-java:*` skills directly in Claude Code if you'd
rather drive one step yourself. In Codex, the corresponding entrypoints are
`$minecraft-java:minecraft-builder` and `$minecraft-java:minecraft-mcp-setup`;
the underlying leaf skills keep their shared names and instructions.

## State model

The builder keeps **persistent state in the Minecraft world**, not in your
workspace — a project folder is useful only while you're working in it, but the
world travels everywhere:

- **Blueprints** are saved as named structure templates (`mcb:<project>_<element>`)
  via the `structure_*` tools, so build elements can be placed, copied, and
  iterated later.
- A **registry** — vanilla command storage at `mcbuilder:registry`, holding a
  [TOON](https://toonformat.dev/) document (read/written with the
  `data_storage_*` tools) — records every project and build (element, structure,
  coordinates, dimension, status, revision). Any future session reads it back
  and can pick up where the last left off.

Local files under `.minecraft-builder/<project>/` (requirements, survey, plan)
are treated as throwaway scratch — Markdown for prose, TOON for structured
data. The `exec-reflect` skill records only *process lessons* in project memory,
never build data.

## MCP connection

The Claude Code marketplace entry remains opt-in: `setup-connect` registers the
MCP server for the user's chosen endpoint and posture. The Codex manifest
includes the safe no-auth localhost defaults, while remote/authenticated users
should configure their endpoint and bearer-token environment variable as shown
in [`reference/mcp/codex-connection.md`](reference/mcp/codex-connection.md).

For a **single-player** install the mod listens on `http://127.0.0.1:8765/mcp`
with no authentication — just the URL is needed. For a **dedicated/remote**
server the mod generates a bearer token on first boot; pass it via an
environment variable so it stays out of version control.
[`.mcp.json.example`](.mcp.json.example) in this repo is a reference template
showing both the no-auth localhost form and the token-via-env pattern.

The mod actually exposes **two** servers from one jar: `minecraft-java` (the
world tools, port 8765) and an optional `minecraft-java-client` (inspection —
`view_capture` returns the player's real first-person frame, plus `sense_*` /
`client_status`, port 8766) that runs inside a real rendered client. Connect the
world server always; add the inspection server when a client is running
(single-player serves both from one process). `setup-connect` covers the
server-only, client-only, and server+client patterns, and `exec-inspect` uses
the real-client frame for in-game verification when it's connected.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for conventions and how to validate
changes, [CHANGELOG.md](CHANGELOG.md) for release history, and
[SECURITY.md](SECURITY.md) to report a vulnerability.

## License

MIT — see [LICENSE](LICENSE).
