from openai import OpenAI
from utils.format_data import format_prompt
from utils.html_extractor import get_html
from schemas.ai import AIAnalyzeRequest

client = OpenAI()

class IAScrapeServices:
    def __init__(self, url: str):
        self.url = url

    def get_data(self, data: AIAnalyzeRequest):
        page_html = get_html(self.url)
        prompt = format_prompt(html=page_html, prompt=data.prompt)

        chat = client.chat.completions.create(
            model='gpt-4o-mini',
            messages=[{'role': 'system', 'content': 'Você extrai dados de sites que o usuario pede'},
                      {'role': 'user', 'content': prompt}],
        max_tokens=500,
        temperature=0.1,
        )
        return chat.choices
    

        
        