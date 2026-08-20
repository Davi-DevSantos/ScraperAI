from openai import OpenAI
from utils.format_data import format_prompt
from utils.html_extractor import get_html
from schemas.ai import AIAnalyzeRequest

client = OpenAI()

class IAScrapeServices:
    def __init__(self, url: str, prompt: str):
        self.url = url
        self.prompt = prompt

    def get_data(self, prompt):
        page_html = get_html(self.url)
        prompt = format_prompt(html=page_html, prompt=self.prompt)

        chat = client.chat.completions.create(
            model='gpt-4o-mini',
            messages=[{'role': 'system', 'content': 'Você extrai dados de sites que o usuario pede'},
                      {'role': 'user', 'content': prompt}],
        max_tokens=500,
        temperature=0.1,
        )
        return chat.choices[0].message.content
    

        
        