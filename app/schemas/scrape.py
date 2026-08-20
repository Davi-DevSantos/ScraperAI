from pydantic import BaseModel, Field

class ScrapeRequest(BaseModel):
    url: str
    
class ScrapeResult(BaseModel):
    texto: str 
  