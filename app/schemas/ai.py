"""Schemas de IA — re-exporta ProviderName e lista de provedores."""

from app.schemas.scrape import ProviderName, ScrapeRequest, ScrapeResult

__all__ = ["ProviderName", "ScrapeRequest", "ScrapeResult"]

SUPPORTED_PROVIDERS: list[str] = ["openai", "anthropic", "gemini"]
