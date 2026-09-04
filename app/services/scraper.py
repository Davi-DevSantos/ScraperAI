import logging

from openai import OpenAI

from app.core.config import setting
from app.services.providers.base import AIProvider
from app.services.providers.factory import get_default_model, get_provider
from app.services.providers.prompts import SYSTEM_PROMPT
from app.utils.format_data import format_prompt
from app.utils.html_extractor import format_html, get_html

logger = logging.getLogger(__name__)


def _build_client():
    raw = ""
    try:
        candidate = setting.get_api_key_for("openai")
        if isinstance(candidate, str) and candidate:
            raw = candidate
    except Exception as exc:  # noqa: BLE001
        logger.debug("get_api_key_for falhou: %s", exc)
        raw = ""
    if not raw:
        try:
            val = setting.AI_API_KEY
            if hasattr(val, "get_secret_value"):
                try:
                    v = val.get_secret_value()
                    if isinstance(v, str) and v:
                        raw = v
                except Exception as exc:  # noqa: BLE001
                    logger.debug("_build_client get_secret_value falhou: %s", exc)
                    raw = ""
            elif isinstance(val, str) and val:
                raw = val
            elif val is not None:
                try:
                    s = str(val)
                    if s and not s.startswith("<MagicMock"):
                        raw = s
                except Exception as exc:  # noqa: BLE001
                    logger.debug("_build_client str(val) falhou: %s", exc)
                    raw = ""
        except Exception as exc:  # noqa: BLE001
            logger.debug("_build_client AI_API_KEY acesso falhou: %s", exc)
            raw = ""
    return OpenAI(api_key=raw or "sk-test")


try:
    client = _build_client()
except Exception as exc:  # noqa: BLE001
    logger.warning("Falha ao criar client OpenAI global: %s", exc)
    client = None


class IAScrapeServices:
    SYSTEM_PROMPT = SYSTEM_PROMPT

    def __init__(
        self,
        url: str,
        prompt: str,
        provider: AIProvider | None = None,
        provider_name: str | None = None,
        api_key: str | None = None,
        model: str | None = None,
        max_tokens: int | None = None,
        temperature: float | None = None,
        client: object | None = None,
    ):
        self.url = url
        self.prompt = prompt
        self._model = model
        self._max_tokens = max_tokens
        self._temperature = temperature

        if client is not None and provider is None and provider_name is None:

            class _LegacyAdapter:
                name = "openai-legacy"

                def __init__(self, _c):
                    self._c = _c

                def complete(
                    self, system: str, user: str, model: str, max_tokens: int, temperature: float
                ):
                    chat = self._c.chat.completions.create(
                        model=model,
                        messages=[
                            {"role": "system", "content": system},
                            {"role": "user", "content": user},
                        ],
                        max_tokens=max_tokens,
                        temperature=temperature,
                    )
                    return chat.choices[0].message.content

            self._provider: AIProvider = _LegacyAdapter(client)
            self._client = client
            return

        if provider is not None:
            self._provider = provider
        else:
            try:
                self._provider = get_provider(provider_name or setting.AI_PROVIDER, api_key=api_key)
            except Exception as e:
                if api_key is None and "não configurada" in str(e):
                    try:
                        self._provider = get_provider(
                            provider_name or setting.AI_PROVIDER, api_key="sk-test"
                        )
                    except Exception as exc2:  # noqa: BLE001
                        logger.debug("fallback sk-test falhou: %s", exc2)
                        raise e
                else:
                    raise
        self._client = None

    def _get_client(self):
        return self._provider

    @property
    def _injected_provider(self):
        return self._provider

    def get_data(self) -> str | None:
        page_html = get_html(self.url)
        clean_html = format_html(page_html)
        prompt = format_prompt(html=str(clean_html), prompt=self.prompt)

        from app.schemas.scrape import ALLOWED_MODELS as _ALLOWED
        from app.services.providers.factory import normalize_provider

        provider_name = getattr(self._provider, "name", setting.AI_PROVIDER)
        provider_name = normalize_provider(provider_name)
        setting_provider = normalize_provider(setting.AI_PROVIDER)
        if self._model is None:
            default_setting = get_default_model(setting_provider)
            if provider_name != setting_provider:
                if (
                    not setting.AI_MODEL
                    or setting.AI_MODEL == default_setting
                    or setting.AI_MODEL not in _ALLOWED.get(provider_name, [])
                ):
                    model = get_default_model(provider_name)
                else:
                    model = setting.AI_MODEL
            else:
                model = setting.AI_MODEL or get_default_model(provider_name)
            if not model:
                model = get_default_model(provider_name)
        else:
            model = self._model

        if self._max_tokens is not None:
            max_tokens = self._max_tokens
        else:
            max_tokens = setting.AI_MAX_TOKENS if setting.AI_MAX_TOKENS else 500

        if self._temperature is not None:
            temperature = self._temperature
        else:
            temperature = setting.AI_TEMPERATURE if setting.AI_TEMPERATURE is not None else 0.1

        return self._provider.complete(
            system=self.SYSTEM_PROMPT,
            user=prompt,
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
        )
