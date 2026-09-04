from app.core.config import setting
from app.core.exceptions import InvalidError
from app.services.providers.anthropic_provider import AnthropicProvider
from app.services.providers.base import AIProvider
from app.services.providers.gemini_provider import GeminiProvider
from app.services.providers.openai_provider import OpenAIProvider

_PROVIDER_MAP: dict[str, type[AIProvider]] = {
    "openai": OpenAIProvider,
    "anthropic": AnthropicProvider,
    "gemini": GeminiProvider,
    "google": GeminiProvider,
}

DEFAULT_MODELS: dict[str, str] = {
    "openai": "gpt-4o-mini",
    "anthropic": "claude-3-5-sonnet-latest",
    "gemini": "gemini-2.5-flash",
}

AVAILABLE_MODELS: dict[str, list[str]] = {
    "openai": [
        "gpt-4o-mini",
        "gpt-4o",
        "gpt-4.1-mini",
        "gpt-4.1",
        "o1-mini",
        "o3-mini",
    ],
    "anthropic": [
        "claude-3-5-sonnet-latest",
        "claude-3-5-haiku-latest",
        "claude-3-opus-latest",
        "claude-3-haiku-20240307",
    ],
    "gemini": [
        "gemini-2.5-pro",
        "gemini-2.5-flash",
        "gemini-2.5-flash-lite",
        "gemini-3-pro",
        "gemini-3-flash",
        "gemini-3.1-pro",
    ],
}

def normalize_provider(name: str | None) -> str:
    raw = (name or setting.AI_PROVIDER or "openai").strip().lower()
    if raw == "google":
        return "gemini"
    if raw == "openai-legacy":
        return "openai"
    return raw

def get_provider(name: str | None = None, api_key: str | None = None) -> AIProvider:
    provider_name = normalize_provider(name)
    cls = _PROVIDER_MAP.get(provider_name)
    if cls is None:
        valid = ", ".join(sorted({k for k in _PROVIDER_MAP if k != "google"}))
        raise InvalidError(f"Provedor '{provider_name}' inválido. Use um de: {valid}")

    effective_key = api_key
    if not effective_key:
        effective_key = setting.get_api_key_for(provider_name)

    return cls(api_key=effective_key)

def get_default_model(provider_name: str | None = None) -> str:
    pn = normalize_provider(provider_name)
    return DEFAULT_MODELS.get(pn, setting.AI_MODEL or "gpt-4o-mini")

def get_available_models(provider_name: str | None = None) -> list[str] | dict[str, list[str]]:
    if provider_name:
        pn = normalize_provider(provider_name)
        return AVAILABLE_MODELS.get(pn, [])
    return AVAILABLE_MODELS
