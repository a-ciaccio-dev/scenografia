"""Tests for the models CLI command."""

from typer.testing import CliRunner

from scenografia.main import app


runner = CliRunner()


def test_models_lists_configured_model_ids_without_exposing_api_key(monkeypatch):
    """Models command should show per-mode model IDs and never print secrets."""
    monkeypatch.setattr("scenografia.main.Config.get_model_for_mode", lambda mode: f"demo/{mode.value}")
    monkeypatch.setattr("scenografia.main.Config.OPENROUTER_API_KEY", "super-secret-key", raising=False)

    result = runner.invoke(app, ["models"])

    assert result.exit_code == 0
    assert "draft" in result.stdout.lower()
    assert "standard" in result.stdout.lower()
    assert "production" in result.stdout.lower()
    assert "vector-ready" in result.stdout.lower()
    assert "demo/draft" in result.stdout
    assert "demo/standard" in result.stdout
    assert "demo/production" in result.stdout
    assert "demo/vector-ready" in result.stdout
    assert "OPENROUTER_API_KEY" not in result.stdout
    assert "super-secret-key" not in result.stdout


def test_models_shows_safe_placeholder_for_missing_configuration(monkeypatch):
    """Models command should use a clear non-secret placeholder when a model is unset."""
    configured = {
        "draft": None,
        "standard": "demo/standard",
        "production": "",
        "vector-ready": None,
    }
    monkeypatch.setattr(
        "scenografia.main.Config.get_model_for_mode",
        lambda mode: configured[mode.value],
    )

    result = runner.invoke(app, ["models"])

    assert result.exit_code == 0
    assert "not configured" in result.stdout.lower()
    assert "set in .env" in result.stdout.lower()
    assert "demo/standard" in result.stdout