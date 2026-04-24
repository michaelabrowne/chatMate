from pathlib import Path

from chatmate.config import load_app_config


def test_load_app_config(tmp_path: Path, monkeypatch) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        """
app:
  name: TestApp
  system_prompt: "Be helpful"
provider:
  active: lmstudio
  openai:
    model: b
  anthropic:
    model: d
  lmstudio:
    model: f
    base_url: http://localhost:1234/v1
agent:
  search:
    default_root: ./docs
    default_file_type: txt
    case_sensitive: true
""".strip()
    )
    monkeypatch.setenv("OPENAI_API_KEY", "openai-token")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "anthropic-token")
    monkeypatch.setenv("LMSTUDIO_API_KEY", "local-token")

    config = load_app_config(config_path)

    assert config.app.name == "TestApp"
    assert config.provider.active == "lmstudio"
    assert config.provider.lmstudio.base_url == "http://localhost:1234/v1"
    assert config.provider.lmstudio.api_key == "local-token"
    assert config.agent.search.case_sensitive is True
