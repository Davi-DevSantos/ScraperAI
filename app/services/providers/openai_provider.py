from openai import OpenAI

from app.core.config import setting
from app.core.exceptions import InvalidError, ServiceError


class OpenAIProvider:
    name = "openai"

    def __init__(self, api_key: str | None = None):
        key = api_key or setting.get_api_key_for("openai")
        if not key:
            raise ServiceError(
                "OPENAI_API_KEY não configurada. Defina no .env ou envie `api_key` na requisição."
            )

        self._client = OpenAI(api_key=key)

    def complete(
        self,
        system: str,
        user: str,
        model: str,
        max_tokens: int,
        temperature: float,
    ) -> str | None:

        if not model:
            raise InvalidError("model não pode ser vazio para OpenAI")
        try:
            kwargs: dict = {
                "model": model,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                "max_tokens": max_tokens,
                "temperature": temperature,
            }
            chat = None
            for _ in range(3):
                try:
                    chat = self._client.chat.completions.create(**kwargs)
                    break
                except Exception as exc:
                    msg = str(exc).lower()
                    retried = False
                    if "max_tokens" in kwargs and "max_completion_tokens" in msg:
                        kwargs["max_completion_tokens"] = kwargs.pop("max_tokens")
                        retried = True
                    if "temperature" in kwargs and "temperature" in msg and "support" in msg:
                        kwargs.pop("temperature")
                        retried = True
                    if not retried:
                        raise
            if chat is None:
                raise ServiceError("OpenAI error: falha ao completar requisição após retries")
            return chat.choices[0].message.content
        except Exception as e:
            msg = str(e)
            if "api_key" in msg.lower() or "unauthorized" in msg.lower() or "401" in msg:
                raise ServiceError(f"OpenAI auth falhou: {msg}") from e
            if "429" in msg or "rate" in msg.lower():
                raise ServiceError(f"OpenAI rate limit: {msg}") from e
            raise ServiceError(f"OpenAI error: {msg}") from e
