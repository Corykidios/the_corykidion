import os

import pytest

from corykidion.config import Config, load_config
from corykidion.errors import ConfigurationError, SafetyViolation


def test_loopback_endpoint_is_accepted():
    config = Config(endpoint="http://localhost:52341/api", api_key="k")
    assert config.endpoint == "http://localhost:52341/api"


def test_127_0_0_1_is_accepted():
    Config(endpoint="http://127.0.0.1:52341/api", api_key="k")


def test_non_loopback_endpoint_is_rejected_by_default():
    with pytest.raises(SafetyViolation):
        Config(endpoint="http://example.invalid/api", api_key="k")


def test_non_loopback_endpoint_allowed_with_explicit_override():
    config = Config(endpoint="http://example.invalid/api", api_key="k", allow_remote=True)
    assert config.allow_remote is True


def test_missing_api_key_is_a_configuration_error():
    with pytest.raises(ConfigurationError):
        Config(endpoint="http://localhost:52341/api", api_key="")


def test_load_config_from_env(monkeypatch):
    monkeypatch.setenv("CORYKIDION_ENDPOINT", "http://localhost:9999/api")
    monkeypatch.setenv("CORYKIDION_API_KEY", "env-key")
    monkeypatch.delenv("CORYKIDION_BRAIN_ID", raising=False)

    config = load_config()

    assert config.endpoint == "http://localhost:9999/api"
    assert config.api_key == "env-key"
    assert config.default_brain_id is None


def test_load_config_without_endpoint_raises(monkeypatch):
    monkeypatch.delenv("CORYKIDION_ENDPOINT", raising=False)
    monkeypatch.delenv("CORYKIDION_API_KEY", raising=False)

    with pytest.raises(ConfigurationError):
        load_config()


def test_load_config_from_toml_file(tmp_path, monkeypatch):
    monkeypatch.delenv("CORYKIDION_ENDPOINT", raising=False)
    monkeypatch.delenv("CORYKIDION_API_KEY", raising=False)
    toml_path = tmp_path / "config.toml"
    toml_path.write_text(
        'endpoint = "http://localhost:1234/api"\n'
        'api_key = "file-key"\n'
        'default_brain_id = "11111111-1111-1111-1111-111111111111"\n'
    )

    config = load_config(toml_path)

    assert config.endpoint == "http://localhost:1234/api"
    assert config.api_key == "file-key"
    assert config.default_brain_id == "11111111-1111-1111-1111-111111111111"
