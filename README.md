# AIScraper

API de scraping com inteligência artificial.

## Estrutura

```
app/                 # Backend (FastAPI)
  core/              # Configurações (.env) e núcleo
  api/routes/        # Endpoints: health, scrape, ai
  schemas/           # Contratos Pydantic de entrada/saída
  services/          # Lógica: scraper (httpx + BeautifulSoup) e IA
  utils/             # Utilitários
frontend/            # Frontend em HTML/CSS/JS puro (consumo da API)
tests/               # Testes (pytest)
```

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
Copy-Item .env.example .env   # edite as chaves
uvicorn app.main:app --reload
```

Docs da API: http://localhost:8000/docs