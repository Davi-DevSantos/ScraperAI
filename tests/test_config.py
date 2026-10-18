from app.core.config import Settings


def test_placeholder_keys_sao_ignorados(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    s = Settings(_env_file=None, OPENAI_API_KEY="sk-proj-coloque_sua_chave_aqui")
    assert s.get_api_key_for("openai") == ""


def test_chave_real_e_preservada(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    s = Settings(_env_file=None, OPENAI_API_KEY="sk-real-key-123")
    assert s.get_api_key_for("openai") == "sk-real-key-123"


def test_gemini_google_alias_copia_chaves(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    s = Settings(_env_file=None, GOOGLE_API_KEY="AIza-test")
    assert s.get_api_key_for("gemini") == "AIza-test"


def test_provider_google_alias_normalizado(monkeypatch):
    monkeypatch.delenv("AI_PROVIDER", raising=False)
    s = Settings(_env_file=None, AI_PROVIDER="google")
    assert s.AI_PROVIDER == "gemini"
