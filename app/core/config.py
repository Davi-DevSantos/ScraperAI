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

    # ===== CORS (origens permitidas para o frontend) =====
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    # ===== IA =====
    # Provedor padrão (usado quando request não especifica)
    AI_PROVIDER: AIProviderName = "openai"
    AI_MODEL: str = "gpt-4o-mini"
    AI_MAX_TOKENS: int = 2048
    AI_TEMPERATURE: float = 0.2

    # Chaves por provedor — preferir estas; AI_API_KEY mantida por compat.
    OPENAI_API_KEY: SecretStr | str = ""
    ANTHROPIC_API_KEY: SecretStr | str = ""
    GOOGLE_API_KEY: SecretStr | str = ""
    # Alias compat. para GOOGLE_API_KEY
    GEMINI_API_KEY: SecretStr | str = ""
    # Chave genérica deprecated (fallback)
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
            # normaliza "google" -> "gemini"
            if v == "google":
                return "gemini"
        return v

    @model_validator(mode="after")
    def _copy_generic_key(self):
        # Se AI_API_KEY preenchida e chave específica vazia, copia para facilitar migração.
        # Não sobrescreve chave específica já definida.
        generic = self._secret_value(self.AI_API_KEY)
        if generic:
            if not self._secret_value(self.OPENAI_API_KEY) and self.AI_PROVIDER == "openai":
                self.OPENAI_API_KEY = generic
            if not self._secret_value(self.ANTHROPIC_API_KEY) and self.AI_PROVIDER == "anthropic":
                self.ANTHROPIC_API_KEY = generic
            if not self._secret_value(self.GOOGLE_API_KEY) and not self._secret_value(self.GEMINI_API_KEY) and self.AI_PROVIDER == "gemini":
                self.GOOGLE_API_KEY = generic
        # Sincroniza GOOGLE <-> GEMINI
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
        """Retorna chave efetiva para o provider (sem expor no repr)."""
        p = provider.strip().lower()
        if p == "google":
            p = "gemini"
        mapping = {
            "openai": self.OPENAI_API_KEY,
            "anthropic": self.ANTHROPIC_API_KEY,
            "gemini": self.GOOGLE_API_KEY or self.GEMINI_API_KEY,
        }
        # fallback para AI_API_KEY genérica
        key = mapping.get(p, "")
        val = self._secret_value(key)
        if not val:
            val = self._secret_value(self.AI_API_KEY)
        return val


setting = Settings()
