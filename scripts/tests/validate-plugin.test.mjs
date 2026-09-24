// Regression tests for the portability checks in scripts/validate-plugin.mjs.
// Dependency-free: node:test + child_process only.
// Run: node --test scripts/tests/
import { test } from "node:test";
import assert from "node:assert/strict";
import { cpSync, existsSync, mkdtempSync, readFileSync, rmSync, appendFileSync } from "node:fs";
import { execFileSync } from "node:child_process";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const root = join(dirname(fileURLToPath(import.meta.url)), "..", "..");

/** Run the validator inside a copy of the repo, returning {code, output}. */
function runValidator(treeRoot) {
  try {
    const out = execFileSync(
      process.execPath,
      [join(treeRoot, "scripts", "validate-plugin.mjs")],
      { encoding: "utf8", stdio: ["ignore", "pipe", "pipe"] },
    );
    return { code: 0, output: out };
  } catch (e) {
    return { code: e.status, output: `${e.stdout || ""}${e.stderr || ""}` };
  }
}

/** A throwaway copy of the repo (no .git, no scratch state). */
function copyTree(mutate) {
  const dir = mkdtempSync(join(tmpdir(), "mcvalidate-"));
  cpSync(root, dir, {
    recursive: true,
    filter: (src) => !/(^|[/\\])(\.git|\.superpowers|\.minecraft-builder)$/.test(src),
  });
  mutate?.(dir);
  return dir;
}

test("the repository passes its own validator", () => {
  const { code, output } = runValidator(root);
  assert.equal(code, 0, output);
});

test("a missing Hermes connection guide fails the build", () => {
  const dir = copyTree((d) => rmSync(join(d, "reference/mcp/hermes-connection.md")));
  try {
    const { code, output } = runValidator(dir);
    assert.equal(code, 1, `expected failure, got:\n${output}`);
    assert.match(output, /missing host connection guide: reference\/mcp\/hermes-connection\.md/);
  } finally {
    rmSync(dir, { recursive: true, force: true });
  }
});

test("a hyphenated MCP tool prefix in a shared skill fails the build", () => {
  const dir = copyTree((d) =>
    appendFileSync(join(d, "skills/survey-site/SKILL.md"), "\nCall `mcp__minecraft-java__server_get_status`.\n"),
  );
  try {
    const { code, output } = runValidator(dir);
    assert.equal(code, 1, `expected failure, got:\n${output}`);
    assert.match(output, /mcp__minecraft-java/);
  } finally {
    rmSync(dir, { recursive: true, force: true });
  }
});

test("a Claude path token in a shared skill fails the build", () => {
  const dir = copyTree((d) =>
    appendFileSync(join(d, "skills/exec-plan/SKILL.md"), "\nRun `${CLAUDE_PLUGIN_ROOT}/tools/builder/harness.py`.\n"),
  );
  try {
    const { code, output } = runValidator(dir);
    assert.equal(code, 1, `expected failure, got:\n${output}`);
    assert.match(output, /CLAUDE_PLUGIN_ROOT/);
  } finally {
    rmSync(dir, { recursive: true, force: true });
  }
});

test("a missing shared skill from the 30-skill suite fails the build", () => {
  const dir = copyTree((d) => rmSync(join(d, "skills/terrain-ecology"), { recursive: true }));
  try {
    const { code, output } = runValidator(dir);
    assert.equal(code, 1, `expected failure, got:\n${output}`);
    assert.match(output, /terrain-ecology/);
  } finally {
    rmSync(dir, { recursive: true, force: true });
  }
});

// --- the Hermes connection guide must stay true to the code it describes ---

const guidePath = join(root, "reference", "mcp", "hermes-connection.md");

test("the Hermes guide's prefix table matches Hermes's normalization rule", () => {
  const rows = readFileSync(guidePath, "utf8")
    .split("\n")
    .map((l) => l.match(/^\|\s*`([^`]+)`\s*\+\s*`([^`]+)`\s*\|\s*`([^`]+)`\s*\|$/))
    .filter(Boolean);
  assert.ok(rows.length >= 4, `expected the server/tool table, found ${rows.length} rows`);
  for (const [, server, tool, expected] of rows) {
    const derived = `mcp__${server.replaceAll("-", "_")}__${tool}`;
    assert.equal(derived, expected, `${server} + ${tool} documented as ${expected}`);
  }
});

test("the Hermes guide documents the config keys and an absolute skills path", () => {
  const body = readFileSync(guidePath, "utf8");
  assert.match(body, /^\s*external_dirs:/m, "skills.external_dirs block");
  assert.match(body, /^\s*mcp_servers:/m, "mcp_servers block");
  assert.match(body, /\/skills\b/m, "an absolute .../skills path");
  for (const server of ["minecraft-java", "minecraft-java-client"]) {
    assert.ok(body.includes(server), `guide names the ${server} server`);
  }
});

test("the entry skills the Hermes guide promises exist on disk", () => {
  const body = readFileSync(guidePath, "utf8");
  // The guide claims these two are the entry skills; the client server name also
  // matches `minecraft-*`, so match the promise, not the pattern.
  const entry = body.match(/entry skills\s*\(([^)]*)\)/);
  assert.ok(entry, "the guide should name its entry skills");
  const named = [...entry[1].matchAll(/`([^`]+)`/g)].map((m) => m[1]);
  assert.deepEqual(named.sort(), ["minecraft-builder", "minecraft-mcp-setup"]);
  for (const name of named) {
    assert.ok(existsSync(join(root, "skills", name, "SKILL.md")), `skills/${name}/SKILL.md`);
  }
});
