from app.schemas.scrape import ProviderInput, ProviderName, ScrapeRequest, ScrapeResult

__all__ = ["ProviderInput", "ProviderName", "ScrapeRequest", "ScrapeResult"]

SUPPORTED_PROVIDERS: list[str] = ["openai", "anthropic", "gemini"]
