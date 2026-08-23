"""Provedores de IA: abstração multi-provedor (OpenAI, Anthropic, Gemini)."""

from app.services.providers.base import AIProvider
from app.services.providers.factory import get_provider

__all__ = ["AIProvider", "get_provider"]
