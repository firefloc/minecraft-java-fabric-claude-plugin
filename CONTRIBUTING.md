# Contributing

Thanks for your interest in improving the Minecraft Java Claude Code + Codex plugin.

## What's in this repo

This is a dual-host plugin — there is no build step for the markdown content and
no runtime code in the plugin itself. It is made of:

- `.claude-plugin/plugin.json` — the plugin manifest.
- `.claude-plugin/marketplace.json` — the marketplace manifest.
- `.codex-plugin/plugin.json` — the Codex plugin manifest and MCP entries.
- `agents/openai.yaml` — Codex plugin UI metadata.
- `agents/codex-*.md` — compact Codex agent adapters.
- `skills/<name>/SKILL.md` — agent skills, each with YAML frontmatter.
- `agents/<name>.md` — agents, each with YAML frontmatter.
- `skills/minecraft-*/` — thin Codex entrypoints that reuse the shared workflow.

## Checks

Every change must pass the validation CI runs. Run it locally with Node 20+:

```sh
node scripts/validate-plugin.mjs
```

It checks that the manifests and `.mcp.json.example` parse, that every skill
and agent has the required frontmatter, and that skill folder names match the
`name` in their frontmatter.

For the full Codex manifest schema, also run the Codex plugin validator when it
is available in your installation:

```sh
python <codex-install>/skills/.system/plugin-creator/scripts/validate_plugin.py .
```

## Conventions

- **Skills are playbooks for the active host, not docs for the user.** Shared
  skills should describe what to do, what to ask, and what to verify. Keep
  Claude-only frontmatter in the existing shared files for compatibility and
  keep Codex adapters model-neutral.
- **Descriptions drive invocation.** A skill's or agent's `description` is what
  the host matches against to decide when to use it. Make it concrete and
  specific about *when* to trigger.
- **Use the Java MCP tool surface.** Reference tools by their Java names
  (`level_*`, `block_*`, `entity_*`, `structure_*`, `data_storage_*`, …) under
  the server name `minecraft-java`. Never use the Bedrock `mc_*` names.
- One skill per setup phase; keep the four setup skills runnable in order, each
  handing off to the next.
- Keep instructions interactive — do one step, verify, then proceed — and never
  have a skill tell the user to commit a secret.
- Kebab-case names. A skill's `name` must match its folder name.
- Keep the stack in lockstep: the Minecraft version, the Fabric API jar, the
  MCP mod jar, and the values referenced in these skills must stay aligned —
  the mod is built per Minecraft version.
- Keep `minecraft-java` and `minecraft-java-client` as the MCP server names and
  keep the existing Java tool names unchanged. See
  `reference/runtime-portability.md` for host-neutral model and path rules.

## Releasing

Bump `version` in `.claude-plugin/plugin.json` and the marketplace entry, add a
dated section to [CHANGELOG.md](CHANGELOG.md), and tag the commit (`vX.Y.Z`).
The plugin is installed directly from the repository — there is no published
artifact.

## Pull requests

Keep pull requests focused on a single change. Describe what changed and how
you verified it.
