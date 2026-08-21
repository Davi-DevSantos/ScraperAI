from openai import OpenAI
from utils.format_data import format_prompt
from utils.html_extractor import format_html, get_html


client = OpenAI()

class IAScrapeServices:
    def __init__(self, url: str, prompt: str):
        self.url = url
        self.prompt = prompt

    def get_data(self) -> str | None:
        page_html = get_html(self.url)
        clean_html = format_html(page_html)
        prompt = format_prompt(html=str(clean_html), prompt=self.prompt)

        chat = client.chat.completions.create(
            model='gpt-4o-mini',
            messages=[{'role': 'system', 'content': 'Você apenas extrai dados de sites e retorna os dados diretamente em formato json'},
                      {'role': 'user', 'content': prompt}],
        max_tokens=500,
        temperature=0.1,
        )
        return chat.choices[0].message.content
    

        
        