from openai import OpenAI

from app.core.config import setting
from app.utils.format_data import format_prompt
from app.utils.html_extractor import format_html, get_html


def _build_client() -> OpenAI:
    api_key = setting.AI_API_KEY or "sk-test"
    return OpenAI(api_key=api_key)


try:
    client = _build_client()
except Exception:
    client = None  # será criado sob demanda em get_data se necessário


class IAScrapeServices:
    SYSTEM_PROMPT = "Você apenas extrai dados de sites e retorna os dados diretamente em formato json"

    def __init__(self, url: str, prompt: str, client: OpenAI | None = None):
        self.url = url
        self.prompt = prompt
        self._client = client

    def _get_client(self) -> OpenAI:
        if self._client is not None:
            return self._client
        if client is not None:
            return client
        return _build_client()

    def get_data(self) -> str | None:
        page_html = get_html(self.url)
        clean_html = format_html(page_html)
        prompt = format_prompt(html=str(clean_html), prompt=self.prompt)

        openai_client = self._get_client()
        chat = openai_client.chat.completions.create(
            model=setting.AI_MODEL or "gpt-4o-mini",
            messages=[
                {"role": "system", "content": self.SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            max_tokens=setting.AI_MAX_TOKENS if setting.AI_MAX_TOKENS else 500,
            temperature=setting.AI_TEMPERATURE if setting.AI_TEMPERATURE is not None else 0.1,
        )
        return chat.choices[0].message.content
    

        
        
