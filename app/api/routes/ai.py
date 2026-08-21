from fastapi import APIRouter, HTTPException
from app.schemas.scrape import ScrapeRequest, ScrapeResult
from app.services.scraper import IAScrapeServices
from fastapi.responses import JSONResponse

router = APIRouter()

router.post("/scrape", response_model=ScrapeResult)
async def scrape_website(request: ScrapeRequest):
    try:
        scraper = IAScrapeServices(url=request.url, prompt=request.prompt)
        data = scraper.get_data()
        return ScrapeResult(data=str(data))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))