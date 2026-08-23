"""Dependências da API (FastAPI Depends)."""

from typing import Annotated

from fastapi import Header

from app.core.config import setting
from app.services.providers.base import AIProvider
from app.services.providers.factory import get_provider


def get_api_key_from_header(
    x_ai_api_key: Annotated[str | None, Header(alias="X-AI-API-Key")] = None,
) -> str | None:
    return x_ai_api_key


def get_ai_provider(
    provider: str | None = None,
    api_key: str | None = None,
) -> AIProvider:
    """Factory dependency — pode ser sobrescrita em testes."""
    return get_provider(provider or setting.AI_PROVIDER, api_key=api_key)
