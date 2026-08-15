"""Schemas de entrada/saída do scraping."""
from pydantic import BaseModel, Field
# TODO: ScrapeRequest (url, regras de extração)
class ScrapeRequest(BaseModel):
    url: str
    
# TODO: ScrapeResult (titulo, links, textos, stats)
class ScrapeResult(BaseModel):
    texto: str 
  