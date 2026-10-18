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
    "openai": "gpt-6-luna",
    "anthropic": "claude-sonnet-5-5",
    "gemini": "gemini-3.8-flash",
}

AVAILABLE_MODELS: dict[str, list[str]] = {
    "openai": [
        "gpt-6-astra",
        "gpt-6.1-sol",
        "gpt-6-luna",
        "gpt-5.6-sol",
        "gpt-5.6-terra",
        "gpt-5.4-mini",
        "gpt-4.1",
        "gpt-4o-mini",
    ],
    "anthropic": [
        "claude-fable-5-1",
        "claude-opus-5-5",
        "claude-sonnet-5-5",
        "claude-haiku-5-5",
        "claude-sonnet-5",
        "claude-haiku-4-5",
    ],
    "gemini": [
        "gemini-4-argon",
        "gemini-3.8-flash",
        "gemini-3.6-flash",
        "gemini-3.5-flash-lite",
        "gemini-3.1-flash-lite",
        "gemini-3.1-pro-preview",
        "gemini-3-flash-preview",
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
    return DEFAULT_MODELS.get(pn, setting.AI_MODEL or "gpt-6-luna")


def get_available_models(provider_name: str | None = None) -> list[str] | dict[str, list[str]]:
    if provider_name:
        pn = normalize_provider(provider_name)
        return AVAILABLE_MODELS.get(pn, [])
    return AVAILABLE_MODELS
