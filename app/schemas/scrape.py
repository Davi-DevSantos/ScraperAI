from typing import Literal

from pydantic import BaseModel, Field, HttpUrl, SecretStr, model_validator

ProviderName = Literal["openai", "anthropic", "gemini"]


ALLOWED_MODELS: dict[str, list[str]] = {
    "openai": ["gpt-4o-mini", "gpt-4o", "gpt-4.1-mini", "gpt-4.1", "o1-mini", "o3-mini"],
    "anthropic": [
        "claude-3-5-sonnet-latest",
        "claude-3-5-haiku-latest",
        "claude-3-opus-latest",
        "claude-3-haiku-20240307",
    ],
    "gemini": [
        "gemini-2.0-flash",
        "gemini-2.0-flash-exp",
        "gemini-1.5-pro",
        "gemini-1.5-flash",
        "gemini-1.5-flash-8b",
    ],
}

class ScrapeRequest(BaseModel):
    url: HttpUrl = Field(..., description="URL do site a extrair")
    prompt: str = Field(..., description="Prompt que guia a extração", min_length=1)
    provider: ProviderName | None = Field(
        None, description="Provedor de IA (openai | anthropic | gemini). Default do .env se omitido"
    )
    model: str | None = Field(None, description="Modelo específico do provedor (apenas modelos da lista)")
    api_key: SecretStr | None = Field(
        None,
        repr=False,
        description="Chave da API do provedor informada pelo usuário (não é logada). Tem prioridade sobre .env",
    )
    max_tokens: int | None = Field(None, ge=1, le=128000, description="Override de max_tokens")
    temperature: float | None = Field(None, ge=0, le=2, description="Override de temperature")

    @model_validator(mode="after")
    def _validate_model_for_provider(self):
        if self.model is None:
            return self

        allowed = []
        if self.provider:
            allowed = ALLOWED_MODELS.get(self.provider, [])
            if self.model not in allowed:
                raise ValueError(f"Modelo '{self.model}' inválido para provider '{self.provider}'. Opções: {', '.join(allowed)}")
        else:
            all_models = [m for lst in ALLOWED_MODELS.values() for m in lst]
            if self.model not in all_models:
                raise ValueError(f"Modelo '{self.model}' inválido. Opções: {', '.join(all_models)}")
        return self

class ScrapeResult(BaseModel):
    data: str = Field(..., description="Dados extraídos em JSON string")
    provider: str = Field(..., description="Provedor usado")
    model: str = Field(..., description="Modelo usado")
