"""Serviço de scraping (httpx + BeautifulSoup)."""
from openai import OpenAI

client = OpenAI()

class IAScrapeServices:
    def __init__(self, url: str):
        self.url = url
# TODO: Classe ScraperService
# TODO: Método scrape(url) -> baixa HTML e extrai conteúdo/texto/links
# TODO: Suportar limites: páginas máximas, timeout, user-agent (do .env)