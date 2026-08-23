from typing import Annotated

from fastapi import APIRouter, Header, HTTPException

from app.core.config import setting
from app.core.exceptions import InvalidError, ServiceError
from app.schemas.scrape import ScrapeRequest, ScrapeResult
from app.services.providers.factory import (
    AVAILABLE_MODELS,
    DEFAULT_MODELS,
    get_default_model,
    get_provider,
)
from app.services.scraper import IAScrapeServices

router = APIRouter(prefix="/api", tags=["ai"])

@router.post("/scrape", response_model=ScrapeResult)
async def scrape_website(
    request: ScrapeRequest,
    x_ai_api_key: Annotated[str | None, Header(alias="X-AI-API-Key")] = None,
):
    body_key = request.api_key.get_secret_value() if request.api_key else None
    effective_key = body_key or x_ai_api_key

    provider_name = request.provider or setting.AI_PROVIDER
    if provider_name.lower() == "google":
        provider_name = "gemini"

    from app.services.providers.factory import normalize_provider

    _norm_req = normalize_provider(str(provider_name))
    _norm_setting = normalize_provider(setting.AI_PROVIDER)
    if request.model:
        effective_model = request.model
    elif _norm_req != _norm_setting and setting.AI_MODEL in (
        "gpt-4o-mini",
        "gpt-4o",
        "gpt-4",
        "gpt-3.5-turbo",
        "",
    ):
        effective_model = get_default_model(_norm_req)
    else:
        effective_model = setting.AI_MODEL or get_default_model(_norm_req)

    effective_max_tokens = request.max_tokens if request.max_tokens is not None else setting.AI_MAX_TOKENS
    effective_temperature = request.temperature if request.temperature is not None else setting.AI_TEMPERATURE

    try:
        provider = get_provider(str(provider_name), api_key=effective_key)

        scraper = IAScrapeServices(
            url=str(request.url),
            prompt=request.prompt,
            provider=provider,
            model=effective_model,
            max_tokens=effective_max_tokens,
            temperature=effective_temperature,
        )
        data = scraper.get_data()

        return ScrapeResult(
            data=str(data) if data is not None else "",
            provider=str(provider_name),
            model=effective_model,
        )
    except InvalidError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e
    except ServiceError as e:
        msg = str(e).lower()
        if "auth" in msg or "api_key" in msg or "401" in msg or "403" in msg:
            raise HTTPException(status_code=401, detail=str(e)) from e
        if "rate" in msg or "429" in msg or "quota" in msg:
            raise HTTPException(status_code=429, detail=str(e)) from e
        raise HTTPException(status_code=502, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

@router.get("/providers")
async def list_providers():
    return {
        "providers": ["openai", "anthropic", "gemini"],
        "default": setting.AI_PROVIDER,
        "default_models": DEFAULT_MODELS,
        "available_models": AVAILABLE_MODELS,
        "models": DEFAULT_MODELS,
    }
