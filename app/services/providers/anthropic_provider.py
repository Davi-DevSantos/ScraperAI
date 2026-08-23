from app.core.config import setting
from app.core.exceptions import InvalidError, ServiceError
from app.utils.json_parser import strip_markdown_fences

class AnthropicProvider:
    name = "anthropic"

    def __init__(self, api_key: str | None = None):
        key = api_key or setting.get_api_key_for("anthropic")
        if not key:
            raise ServiceError(
                "ANTHROPIC_API_KEY não configurada. Defina no .env ou envie `api_key` na requisição."
            )
        try:
            import anthropic

            self._client = anthropic.Anthropic(api_key=key)
        except ImportError as e:
            raise ServiceError(
                "Pacote `anthropic` não instalado. Adicione `anthropic>=0.30` a requirements.txt/pyproject.toml e instale."
            ) from e

    def complete(
        self,
        system: str,
        user: str,
        model: str,
        max_tokens: int,
        temperature: float,
    ) -> str | None:
        if not model:
            raise InvalidError("model não pode ser vazio para Anthropic")
        try:

            resp = self._client.messages.create(
                model=model,
                system=system,
                messages=[{"role": "user", "content": user}],
                max_tokens=max_tokens,
                temperature=temperature,
            )

            if not resp.content:
                return None
            block = resp.content[0]
            text = getattr(block, "text", None)
            if text is None and isinstance(block, dict):
                text = block.get("text")
            if text is None:
                text = str(block)
            return strip_markdown_fences(text)
        except Exception as e:
            msg = str(e)
            if "api_key" in msg.lower() or "authentication" in msg.lower() or "401" in msg:
                raise ServiceError(f"Anthropic auth falhou: {msg}") from e
            if "429" in msg or "rate" in msg.lower():
                raise ServiceError(f"Anthropic rate limit: {msg}") from e
            raise ServiceError(f"Anthropic error: {msg}") from e
