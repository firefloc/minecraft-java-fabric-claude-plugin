"""Shared MCP endpoint discovery for the Minecraft helper scripts.

The plugin can be driven by Claude Code, Codex, or directly from a shell.  The
host applications keep their MCP settings in different places, so the helper
scripts use the same small compatibility layer instead of each embedding a
Claude-only config reader.

Supported sources, in precedence order, are:

1. ``MINECRAFT_MCP_URL`` (or the client equivalent) and an optional token env
   var;
2. Claude Code's ``~/.claude.json`` (the historical helper precedence);
3. the project ``.mcp.json``;
4. Codex's ``~/.codex/config.toml``;
5. the local world-server default.

The MCP server names and the HTTP transport are intentionally unchanged:
``minecraft-java`` is the world server and ``minecraft-java-client`` is the
optional rendered-client inspection server.
"""
from __future__ import annotations

import json
import os
import re
from pathlib import Path

try:  # Python 3.11+; Codex and current supported environments provide it.
    import tomllib
except ImportError:  # pragma: no cover - only relevant to older Python hosts
    tomllib = None


SERVER_ALIASES = {
    "minecraft-java": ("minecraft-java", "minecraft_java", "minecraft"),
    "minecraft-java-client": (
        "minecraft-java-client",
        "minecraft_java_client",
        "minecraft-client",
    ),
}


def expand(value):
    """Expand ``${VAR}`` and ``${VAR:-default}`` in a config value."""
    if not isinstance(value, str):
        return value

    def replace(match):
        name, default = match.group(1), match.group(2)
        return os.environ.get(name, default if default is not None else "")

    return re.sub(r"\$\{([A-Za-z_][A-Za-z0-9_]*)(?::-([^}]*))?\}", replace, value)


def server_entry(config: dict, server_name: str):
    """Return a named server entry from Claude/JSON or Codex/TOML-shaped data."""
    names = SERVER_ALIASES.get(server_name, (server_name,))
    for key in ("mcpServers", "mcp_servers"):
        servers = config.get(key)
        if isinstance(servers, dict):
            for name in names:
                if name in servers:
                    return servers[name]

    # Claude's global JSON nests project-specific servers under projects.
    for project in (config.get("projects") or {}).values():
        if not isinstance(project, dict):
            continue
        for key in ("mcpServers", "mcp_servers"):
            servers = project.get(key)
            if isinstance(servers, dict):
                for name in names:
                    if name in servers:
                        return servers[name]
    return None


def _load_file(path: Path):
    try:
        if path.suffix.lower() == ".toml":
            if tomllib is None:
                return _load_codex_toml_fallback(path)
            with path.open("rb") as handle:
                return tomllib.load(handle)
        with path.open(encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, ValueError, TypeError):
        return None


def _load_codex_toml_fallback(path: Path):
    """Read the small Codex MCP subset when running on Python 3.10.

    ``tomllib`` was added in Python 3.11, while the toolkit still supports
    Python 3.10. Codex MCP entries only need a table name plus ``url`` and
    ``bearer_token_env_var`` here, so keep a dependency-free fallback for that
    subset rather than making the whole helper layer require a newer Python.
    """
    config = {"mcp_servers": {}}
    current = None
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return None
    for raw in lines:
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        section = re.fullmatch(r"\[\s*mcp_servers\.([^\]]+)\s*\]", line)
        if section:
            name = section.group(1).strip().strip('"')
            current = config["mcp_servers"].setdefault(name, {})
            continue
        if current is None or "=" not in line:
            continue
        key, value = (part.strip() for part in line.split("=", 1))
        if key not in {"url", "bearer_token_env_var"}:
            continue
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        current[key] = value
    return config


def _token_env_name(server_name: str):
    if server_name == "minecraft-java-client":
        return "MINECRAFT_MCP_CLIENT_TOKEN"
    return "MINECRAFT_MCP_TOKEN"


def _headers(entry: dict, server_name: str):
    headers = {
        key: expand(value)
        for key, value in (entry.get("headers") or {}).items()
    }

    # Codex's HTTP MCP config names the token variable rather than storing the
    # token.  Accept that shape alongside the existing Claude/JSON headers.
    token_var = entry.get("bearer_token_env_var")
    token = os.environ.get(token_var, "") if token_var else ""
    if not token:
        token = os.environ.get(_token_env_name(server_name), "")
    if token:
        headers.setdefault("Authorization", f"Bearer {token}")
    return headers


def _env_url_name(server_name: str):
    if server_name == "minecraft-java-client":
        return "MINECRAFT_MCP_CLIENT_URL"
    return "MINECRAFT_MCP_URL"


def load_server_config(
    server_name: str = "minecraft-java",
    default_url: str = "http://localhost:8765/mcp",
    cwd: str | os.PathLike[str] | None = None,
    home: str | os.PathLike[str] | None = None,
):
    """Return ``(url, headers)`` for one of the Minecraft MCP servers."""
    env_url = os.environ.get(_env_url_name(server_name))
    if env_url:
        return expand(env_url), _headers({}, server_name)

    current_dir = Path(cwd) if cwd is not None else Path.cwd()
    home_dir = Path(home) if home is not None else Path.home()
    candidates = (
        home_dir / ".claude.json",
        current_dir / ".mcp.json",
        home_dir / ".codex" / "config.toml",
    )
    for path in candidates:
        config = _load_file(path)
        if not isinstance(config, dict):
            continue
        entry = server_entry(config, server_name)
        if not isinstance(entry, dict):
            continue
        url = expand(entry.get("url") or default_url)
        return url, _headers(entry, server_name)
    return default_url, _headers({}, server_name)


# Backwards-compatible private aliases used by older helper code and external
# scripts that imported these names before the readers were consolidated.
_expand = expand
