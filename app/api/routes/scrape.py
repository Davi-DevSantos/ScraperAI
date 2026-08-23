"""Endpoints de scraping (legado) — redireciona para /api/scrape."""

from fastapi import APIRouter

# Mantido para compatibilidade; lógica real está em app/api/routes/ai.py
router = APIRouter(prefix="/api", tags=["scrape"])
