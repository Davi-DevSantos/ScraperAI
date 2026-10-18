from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_check():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok", "version": "1.0.0"}


def test_root():
    r = client.get("/")
    assert r.status_code == 200
    data = r.json()
    assert data["health"] == "/health"
    assert data["providers"] == "/api/providers"
    assert data["scrape"] == "POST /api/scrape"


def test_providers_list():
    r = client.get("/api/providers")
    assert r.status_code == 200
    data = r.json()
    assert set(data["providers"]) == {"openai", "anthropic", "gemini"}
    assert "default_models" in data
    assert "available_models" in data
    assert data["default_models"]["openai"] == "gpt-6-luna"
    assert "gpt-6-luna" in data["available_models"]["openai"]


def test_scrape_invalid_model_422():
    r = client.post(
        "/api/scrape",
        json={
            "url": "https://example.com",
            "prompt": "test",
            "provider": "openai",
            "model": "modelo-invalido",
            "api_key": "sk-test",
        },
    )
    assert r.status_code == 422
    assert "inválido" in r.text


def test_scrape_mock_success_body_key():
    import app.services.scraper as sc

    with (
        patch.object(sc, "get_html", return_value="<html>hi</html>"),
        patch.object(
            sc, "format_html", return_value=MagicMock(__str__=lambda s: "<html>clean</html>")
        ),
        patch.object(sc, "format_prompt", return_value="prompt fmt"),
        patch("app.api.routes.ai.get_provider") as mock_gp,
    ):
        mock_prov = MagicMock()
        mock_prov.complete.return_value = '{"ok":1}'
        mock_prov.name = "openai"
        mock_gp.return_value = mock_prov
        r = client.post(
            "/api/scrape",
            json={
                "url": "https://example.com",
                "prompt": "extraia",
                "provider": "openai",
                "model": "gpt-6-luna",
                "api_key": "sk-test",
            },
        )
        assert r.status_code == 200
        assert r.json()["data"] == '{"ok":1}'
        assert r.json()["provider"] == "openai"
        mock_prov.complete.assert_called_once()


def test_scrape_mock_success_header_key():
    import app.services.scraper as sc

    with (
        patch.object(sc, "get_html", return_value="<html>hi</html>"),
        patch.object(
            sc, "format_html", return_value=MagicMock(__str__=lambda s: "<html>clean</html>")
        ),
        patch.object(sc, "format_prompt", return_value="prompt fmt"),
        patch("app.api.routes.ai.get_provider") as mock_gp,
    ):
        mock_prov = MagicMock()
        mock_prov.complete.return_value = '{"ok":1}'
        mock_prov.name = "gemini"
        mock_gp.return_value = mock_prov
        r = client.post(
            "/api/scrape",
            json={
                "url": "https://example.com",
                "prompt": "extraia",
                "provider": "gemini",
                "model": "gemini-3.8-flash",
            },
            headers={"X-AI-API-Key": "AIza-test"},
        )
        assert r.status_code == 200
        assert r.json()["provider"] == "gemini"


def test_scrape_google_alias_normaliza_para_gemini():
    import app.services.scraper as sc

    with (
        patch.object(sc, "get_html", return_value="<html>hi</html>"),
        patch.object(
            sc, "format_html", return_value=MagicMock(__str__=lambda s: "<html>clean</html>")
        ),
        patch.object(sc, "format_prompt", return_value="prompt fmt"),
        patch("app.api.routes.ai.get_provider") as mock_gp,
    ):
        mock_prov = MagicMock()
        mock_prov.complete.return_value = '{"ok":1}'
        mock_prov.name = "gemini"
        mock_gp.return_value = mock_prov
        r = client.post(
            "/api/scrape",
            json={
                "url": "https://example.com",
                "prompt": "extraia",
                "provider": "google",
                "model": "gemini-3.8-flash",
                "api_key": "AIza-test",
            },
        )
        assert r.status_code == 200
        assert r.json()["provider"] == "gemini"
        mock_gp.assert_called_once()


def test_scrape_request_google_alias_valida_modelo_do_gemini():
    from pydantic import ValidationError

    from app.schemas.scrape import ScrapeRequest

    req = ScrapeRequest(
        url="https://example.com",
        prompt="p",
        provider="google",
        model="gemini-3.8-flash",
    )
    assert req.provider == "gemini"

    with pytest.raises(ValidationError):
        ScrapeRequest(
            url="https://example.com",
            prompt="p",
            provider="google",
            model="gpt-6-luna",
        )


def test_scrape_default_model_logic_openai_to_gemini():
    """Se provider muda e setting AI_MODEL é default openai, deve usar default gemini."""
    import app.services.scraper as sc

    with (
        patch.object(sc, "get_html", return_value="<html>hi</html>"),
        patch.object(sc, "format_html", return_value=MagicMock(__str__=lambda s: "clean")),
        patch.object(sc, "format_prompt", return_value="p"),
        patch("app.api.routes.ai.get_provider") as mock_gp,
        patch("app.api.routes.ai.setting") as mock_setting,
    ):
        mock_setting.AI_PROVIDER = "openai"
        mock_setting.AI_MODEL = "gpt-6-luna"
        mock_setting.AI_MAX_TOKENS = 2048
        mock_setting.AI_TEMPERATURE = 0.2

        mock_prov = MagicMock()
        mock_prov.complete.return_value = '{"x":1}'
        mock_prov.name = "gemini"
        mock_gp.return_value = mock_prov

        r = client.post(
            "/api/scrape",
            json={
                "url": "https://example.com",
                "prompt": "extraia",
                "provider": "gemini",
                "api_key": "sk-test",
            },
        )
        assert r.status_code == 200
        # provider solicitado é gemini, sem model no body => deve usar default gemini, não gpt-6-luna
        assert r.json()["model"] == "gemini-3.8-flash"
