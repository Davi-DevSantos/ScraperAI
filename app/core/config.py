from typing import Literal

from pydantic import SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

AIProviderName = Literal["openai", "anthropic", "gemini"]

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ===== API =====
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_DEBUG: bool = True

    # ===== CORS =====
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    # ===== IA =====
    AI_PROVIDER: AIProviderName = "openai"
    AI_MODEL: str = "gpt-4o-mini"
    AI_MAX_TOKENS: int = 2048
    AI_TEMPERATURE: float = 0.2

    OPENAI_API_KEY: SecretStr | str = ""
    ANTHROPIC_API_KEY: SecretStr | str = ""
    GOOGLE_API_KEY: SecretStr | str = ""
    GEMINI_API_KEY: SecretStr | str = ""
    AI_API_KEY: SecretStr | str = ""

    # ===== Scraper =====
    SCRAPER_TIMEOUT: int = 30
    SCRAPER_USER_AGENT: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    SCRAPER_MAX_PAGES: int = 10

    @field_validator("AI_PROVIDER", mode="before")
    @classmethod
    def _normalize_provider(cls, v: str) -> str:
        if isinstance(v, str):
            v = v.strip().lower()
            if v == "google":
                return "gemini"
        return v

    @model_validator(mode="after")
    def _copy_generic_key(self):
        generic = self._secret_value(self.AI_API_KEY)
        if generic:
            if not self._secret_value(self.OPENAI_API_KEY) and self.AI_PROVIDER == "openai":
                self.OPENAI_API_KEY = generic
            if not self._secret_value(self.ANTHROPIC_API_KEY) and self.AI_PROVIDER == "anthropic":
                self.ANTHROPIC_API_KEY = generic
            if not self._secret_value(self.GOOGLE_API_KEY) and not self._secret_value(self.GEMINI_API_KEY) and self.AI_PROVIDER == "gemini":
                self.GOOGLE_API_KEY = generic
        if self._secret_value(self.GEMINI_API_KEY) and not self._secret_value(self.GOOGLE_API_KEY):
            self.GOOGLE_API_KEY = self._secret_value(self.GEMINI_API_KEY)
        elif self._secret_value(self.GOOGLE_API_KEY) and not self._secret_value(self.GEMINI_API_KEY):
            self.GEMINI_API_KEY = self._secret_value(self.GOOGLE_API_KEY)
        return self

    @staticmethod
    def _secret_value(v: SecretStr | str) -> str:
        if isinstance(v, SecretStr):
            return v.get_secret_value() if v.get_secret_value() else ""
        return v or ""

    def get_api_key_for(self, provider: str) -> str:
        p = provider.strip().lower()
        if p == "google":
            p = "gemini"
        mapping = {
            "openai": self.OPENAI_API_KEY,
            "anthropic": self.ANTHROPIC_API_KEY,
            "gemini": self.GOOGLE_API_KEY or self.GEMINI_API_KEY,
        }
        key = mapping.get(p, "")
        val = self._secret_value(key)
        if not val:
            val = self._secret_value(self.AI_API_KEY)
        return val

setting = Settings()
