from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api.routes import ai, health
from app.core.config import setting

app = FastAPI(
    title="AIScraper",
    description="API de scraping com IA — multi-provedor OpenAI/Anthropic/Gemini. Envie sua própria API key por requisição.",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=setting.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(health.router)
app.include_router(ai.router)

frontend_path = Path(__file__).parent.parent / "frontend"
if frontend_path.exists():
    app.mount("/app", StaticFiles(directory=str(frontend_path), html=True), name="frontend")


@app.get("/", include_in_schema=False)
async def root():
    return JSONResponse(
        {
            "name": "AIScraper",
            "version": "0.1.0",
            "docs": "/docs",
            "health": "/health",
            "providers": "/api/providers",
            "scrape": "POST /api/scrape",
            "frontend": "/app/",
        }
    )
