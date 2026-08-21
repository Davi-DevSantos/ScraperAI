from pydantic import BaseModel, Field, HTTPUrl

class ScrapeRequest(BaseModel):
    url: HTTPUrl = Field(..., description="The URL of the website to scrape")
    prompt: str = Field(..., description="The prompt to guide the scraping process")

class ScrapeResult(BaseModel):
    data: str = Field(..., description="The extracted data from the website")
  