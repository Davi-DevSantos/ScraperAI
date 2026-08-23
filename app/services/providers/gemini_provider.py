from app.core.config import setting
from app.core.exceptions import InvalidError, ServiceError
from app.utils.json_parser import strip_markdown_fences

class GeminiProvider:
    name = "gemini"

    def __init__(self, api_key: str | None = None):
        key = api_key or setting.get_api_key_for("gemini")
        if not key:
            raise ServiceError(
                "GOOGLE_API_KEY (ou GEMINI_API_KEY) não configurada. Defina no .env ou envie `api_key` na requisição."
            )
        try:
            import google.generativeai as genai

            genai.configure(api_key=key)
            self._genai = genai
            self._api_key = key
        except ImportError as e:
            raise ServiceError(
                "Pacote `google-generativeai` não instalado. Adicione `google-generativeai>=0.8` e instale."
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
            raise InvalidError("model não pode ser vazio para Gemini")
        try:


            try:
                mdl = self._genai.GenerativeModel(
                    model_name=model,
                    system_instruction=system,
                )
            except TypeError:

                mdl = self._genai.GenerativeModel(model_name=model)
                user = f"{system}\n\n{user}"

            resp = mdl.generate_content(
                user,
                generation_config={
                    "max_output_tokens": max_tokens,
                    "temperature": temperature,
                },
            )

            text = getattr(resp, "text", None)
            if text is None:

                try:
                    text = resp.candidates[0].content.parts[0].text
                except Exception:
                    text = None
            return strip_markdown_fences(text)
        except Exception as e:
            msg = str(e)
            if "api_key" in msg.lower() or "api key" in msg.lower() or "401" in msg or "403" in msg:
                raise ServiceError(f"Gemini auth falhou: {msg}") from e
            if "429" in msg or "quota" in msg.lower() or "rate" in msg.lower():
                raise ServiceError(f"Gemini rate limit: {msg}") from e
            raise ServiceError(f"Gemini error: {msg}") from e
