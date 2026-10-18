from typing import Literal

from pydantic import BaseModel, Field, HttpUrl, SecretStr, model_validator

ProviderName = Literal["openai", "anthropic", "gemini"]
ProviderInput = Literal["openai", "anthropic", "gemini", "google"]


ALLOWED_MODELS: dict[str, list[str]] = {
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


class ScrapeRequest(BaseModel):
    url: HttpUrl = Field(..., description="URL do site a extrair")
    prompt: str = Field(..., description="Prompt que guia a extração", min_length=1)
    provider: ProviderInput | None = Field(
        None,
        description="Provedor de IA (openai | anthropic | gemini; 'google' é alias de gemini). Default do .env se omitido",
    )
    model: str | None = Field(
        None, description="Modelo específico do provedor (apenas modelos da lista)"
    )
    api_key: SecretStr | None = Field(
        None,
        repr=False,
        description="Chave da API do provedor informada pelo usuário (não é logada). Tem prioridade sobre .env",
    )
    max_tokens: int | None = Field(None, ge=1, le=128000, description="Override de max_tokens")
    temperature: float | None = Field(None, ge=0, le=2, description="Override de temperature")

    @model_validator(mode="after")
    def _normalize_provider_e_valida_modelo(self):
        if self.provider == "google":
            self.provider = "gemini"

        if self.model is None:
            return self

        allowed = []
        if self.provider:
            allowed = ALLOWED_MODELS.get(self.provider, [])
            if self.model not in allowed:
                raise ValueError(
                    f"Modelo '{self.model}' inválido para provider '{self.provider}'. Opções: {', '.join(allowed)}"
                )
        else:
            all_models = [m for lst in ALLOWED_MODELS.values() for m in lst]
            if self.model not in all_models:
                raise ValueError(f"Modelo '{self.model}' inválido. Opções: {', '.join(all_models)}")
        return self


class ScrapeResult(BaseModel):
    data: str = Field(..., description="Dados extraídos em JSON string")
    provider: str = Field(..., description="Provedor usado")
    model: str = Field(..., description="Modelo usado")
