"""MCP endpoint discovery works with both Claude and Codex config shapes."""
import json

from mcp_config import load_server_config


def test_project_json_is_used_and_expands_environment(tmp_path, monkeypatch):
    for name in (
        "MINECRAFT_MCP_URL",
        "MINECRAFT_MCP_TOKEN",
        "MINECRAFT_MCP_CLIENT_URL",
        "MINECRAFT_MCP_CLIENT_TOKEN",
    ):
        monkeypatch.delenv(name, raising=False)
    project = tmp_path / ".mcp.json"
    project.write_text(
        json.dumps(
            {
                "mcpServers": {
                    "minecraft-java": {
                        "type": "http",
                        "url": "${WORLD_URL:-http://localhost:8765/mcp}",
                        "headers": {
                            "Authorization": "Bearer ${WORLD_TOKEN}",
                        },
                    }
                }
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("WORLD_URL", "https://example.test/world/mcp")
    monkeypatch.setenv("WORLD_TOKEN", "secret")

    assert load_server_config(cwd=tmp_path, home=tmp_path / "home") == (
        "https://example.test/world/mcp",
        {"Authorization": "Bearer secret"},
    )


def test_codex_toml_and_bearer_token_are_supported(tmp_path, monkeypatch):
    for name in (
        "MINECRAFT_MCP_URL",
        "MINECRAFT_MCP_TOKEN",
        "MINECRAFT_MCP_CLIENT_URL",
        "MINECRAFT_MCP_CLIENT_TOKEN",
    ):
        monkeypatch.delenv(name, raising=False)
    home = tmp_path / "home"
    (home / ".codex").mkdir(parents=True)
    (home / ".codex" / "config.toml").write_text(
        '[mcp_servers.minecraft-java]\n'
        'url = "https://example.test/world/mcp"\n'
        'bearer_token_env_var = "CODEX_MINECRAFT_TOKEN"\n',
        encoding="utf-8",
    )
    monkeypatch.setenv("CODEX_MINECRAFT_TOKEN", "codex-secret")

    assert load_server_config(cwd=tmp_path / "project", home=home) == (
        "https://example.test/world/mcp",
        {"Authorization": "Bearer codex-secret"},
    )


def test_client_uses_its_own_names_and_environment_overrides(tmp_path, monkeypatch):
    monkeypatch.delenv("MINECRAFT_MCP_URL", raising=False)
    monkeypatch.delenv("MINECRAFT_MCP_TOKEN", raising=False)
    monkeypatch.setenv(
        "MINECRAFT_MCP_CLIENT_URL", "http://127.0.0.1:9876/mcp"
    )
    monkeypatch.setenv("MINECRAFT_MCP_CLIENT_TOKEN", "client-secret")

    assert load_server_config(
        server_name="minecraft-java-client",
        default_url="http://127.0.0.1:8766/mcp",
        cwd=tmp_path,
        home=tmp_path,
    ) == (
        "http://127.0.0.1:9876/mcp",
        {"Authorization": "Bearer client-secret"},
    )
