#!/usr/bin/env python3
"""Hermes Agent portability smoke test for this plugin.

Static checks always run; live checks run when their prerequisite is present and
are reported SKIP otherwise, so the script is safe to run anywhere.

    python3 scripts/hermes-smoke.py                 # static + live if reachable
    HERMES_HOME=... python3 scripts/hermes-smoke.py # against a test profile

Exit 0 when nothing FAILed. See docs/portability-smoke-test.md for the full
matrix this feeds.
"""
import json
import os
import re
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GUIDE = ROOT / "reference" / "mcp" / "hermes-connection.md"
DEFAULT_URL = os.environ.get("MINECRAFT_MCP_URL", "http://127.0.0.1:8765/mcp")

results = []


def record(name, verdict, detail=""):
    results.append((name, verdict, detail))
    print(f"{verdict:<5} {name}" + (f" — {detail}" if detail else ""))


# --- static: the guide and the suite it promises -----------------------------


def check_suite():
    skills = sorted(p.name for p in (ROOT / "skills").iterdir() if (p / "SKILL.md").is_file())
    record("30-skill suite on disk", "PASS" if len(skills) == 30 else "FAIL", f"{len(skills)} skills")
    body = GUIDE.read_text(encoding="utf-8")
    for skill in re.findall(r"entry skills\s*\(([^)]*)\)", body):
        for name in re.findall(r"`([^`]+)`", skill):
            ok = (ROOT / "skills" / name / "SKILL.md").is_file()
            record(f"entry skill {name}", "PASS" if ok else "FAIL")


def check_guide_prefix_rule():
    rows = re.findall(
        r"^\|\s*`([^`]+)`\s*\+\s*`([^`]+)`\s*\|\s*`([^`]+)`\s*\|$",
        GUIDE.read_text(encoding="utf-8"),
        re.M,
    )
    bad = [r for r in rows if f"mcp__{r[0].replace('-', '_')}__{r[1]}" != r[2]]
    record(
        "guide prefix table matches Hermes normalization",
        "PASS" if rows and not bad else "FAIL",
        f"{len(rows)} rows, {len(bad)} wrong",
    )


# --- live: discovery through the Hermes CLI ----------------------------------


def check_hermes_discovery():
    if not shutil.which("hermes"):
        return record("Hermes CLI discovery", "SKIP", "hermes not on PATH")
    try:
        out = subprocess.run(
            ["hermes", "skills", "list", "--source", "local"],
            capture_output=True, text=True, timeout=180,
        ).stdout
    except Exception as exc:  # noqa: BLE001 - report, never crash the suite
        return record("Hermes CLI discovery", "FAIL", str(exc))
    names = {p.name for p in (ROOT / "skills").iterdir() if (p / "SKILL.md").is_file()}
    seen = {n for n in names if re.search(rf"\b{re.escape(n)}\b", out)}
    record(
        "Hermes CLI discovery",
        "PASS" if len(seen) == len(names) else "FAIL",
        f"{len(seen)}/{len(names)} skills visible"
        + ("" if os.environ.get("HERMES_HOME") else " (profile default; set HERMES_HOME to test another)"),
    )


# --- live: MCP endpoint, no third-party dependency ---------------------------


def rpc(url, method, params, session=None, notify=False, timeout=30):
    payload = {"jsonrpc": "2.0", "method": method, "params": params}
    if not notify:
        payload["id"] = 1
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
    }
    if session:
        headers["Mcp-Session-Id"] = session
    if (token := os.environ.get("MINECRAFT_MCP_TOKEN")):
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(
        url, data=json.dumps(payload).encode(), headers=headers, method="POST"
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raw = resp.read().decode()
        sid = resp.headers.get("Mcp-Session-Id")
    if not raw.strip():
        return None, sid
    data = next((l[5:].strip() for l in raw.splitlines() if l.startswith("data:")), raw)
    return json.loads(data), sid


def check_live_mcp():
    try:
        init, sid = rpc(DEFAULT_URL, "initialize", {
            "protocolVersion": "2025-06-18",
            "capabilities": {},
            "clientInfo": {"name": "hermes-smoke", "version": "1"},
        })
        rpc(DEFAULT_URL, "notifications/initialized", {}, session=sid, notify=True)
    except (urllib.error.URLError, OSError, ValueError) as exc:
        return record("live MCP endpoint", "SKIP", f"{DEFAULT_URL} unreachable ({exc})")
    server = (init or {}).get("result", {}).get("serverInfo", {})
    if not server:
        return record("live MCP handshake", "FAIL", "initialize returned nothing usable")
    record("live MCP handshake", "PASS", f"{server.get('name')} {server.get('version')}")
    listing, _ = rpc(DEFAULT_URL, "tools/list", {}, session=sid)
    tools = {t["name"] for t in (listing or {}).get("result", {}).get("tools", [])}
    record("tools/list", "PASS" if tools else "FAIL", f"{len(tools)} tools")
    for tool, args in (("server_get_status", {}),
                       ("level_get_info", {"dimension": "minecraft:overworld"})):
        if tool not in tools:
            record(f"call {tool}", "FAIL", "not exposed by the server")
            continue
        reply, _ = rpc(DEFAULT_URL, "tools/call", {"name": tool, "arguments": args}, session=sid)
        reply = reply or {}
        text = json.dumps(reply.get("result", {}))[:160]
        record(f"call {tool}", "PASS" if "error" not in reply else "FAIL", text)
    for tool in ("client_status", "view_capture"):
        record(
            f"rendered-client tool {tool}",
            "INFO",
            "exposed on the world server" if tool in tools
            else "absent — the workflow must report server-only inspection",
        )


def main():
    if not GUIDE.is_file():
        print(f"FAIL  missing {GUIDE}")
        return 1
    check_suite()
    check_guide_prefix_rule()
    check_hermes_discovery()
    check_live_mcp()
    failed = [n for n, v, _ in results if v == "FAIL"]
    skipped = [n for n, v, _ in results if v in ("SKIP", "INFO")]
    print(f"\n{len(results) - len(failed) - len(skipped)} passed, "
          f"{len(failed)} failed, {len(skipped)} skipped/info")
    if failed:
        print("failed: " + ", ".join(failed))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
