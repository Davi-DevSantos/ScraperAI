# AIScraper

API de scraping com inteligência artificial — **multi-provedor** (OpenAI, Anthropic, Gemini) com suporte a **chave por requisição** do usuário.

Extrai HTML com Playwright + BeautifulSoup e usa LLM para retornar JSON estruturado.

## Estrutura

```
app/                      # Backend (FastAPI)
  core/config.py          # Settings por .env (3 chaves por provedor)
  api/routes/
    health.py             # GET /health
    ai.py                 # POST /api/scrape  +  GET /api/providers
  schemas/scrape.py       # ScrapeRequest/ScrapeResult (provider, api_key, model...)
  services/
    scraper.py            # IAScrapeServices (agnóstico, delega para provider)
    providers/
      base.py             # AIProvider Protocol
      factory.py          # get_provider() + get_default_model()
      openai_provider.py
      anthropic_provider.py
      gemini_provider.py
      prompts.py          # SYSTEM_PROMPT
  utils/
    html_extractor.py     # Playwright + BeautifulSoup
    format_data.py        # format_prompt
    json_parser.py        # strip_markdown_fences
frontend/                 # HTML/CSS/JS puro (seletor de provedor + campo API key)
tests/                    # pytest
```

## Requisitos

- Python >= 3.11
- Playwright browsers (`playwright install chromium`)

## Setup

### Linux / macOS
```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
# ou
pip install -r requirements.txt
playwright install chromium
cp .env.example .env   # edite as chaves
uvicorn app.main:app --reload
```

### Windows PowerShell
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
playwright install chromium
Copy-Item .env.example .env   # edite as chaves
uvicorn app.main:app --reload
```

Docs: http://localhost:8000/docs — Health: http://localhost:8000/health

## Variáveis de Ambiente (.env)

| Var | Default | Descrição |
|-----|---------|-----------|
| `API_HOST` | `0.0.0.0` | host |
| `API_PORT` | `8000` | porta |
| `CORS_ORIGINS` | `["http://localhost:3000",...]` | origins |
| `AI_PROVIDER` | `openai` | `openai` \| `anthropic` \| `gemini` (`google` alias) |
| `AI_MODEL` | `gpt-4o-mini` | modelo default do provider padrão |
| `AI_MAX_TOKENS` | `2048` | |
| `AI_TEMPERATURE` | `0.2` | `0..2` |
| `OPENAI_API_KEY` |  | https://platform.openai.com/api-keys |
| `ANTHROPIC_API_KEY` |  | https://console.anthropic.com/settings/keys |
| `GOOGLE_API_KEY` / `GEMINI_API_KEY` |  | https://aistudio.google.com/app/apikey |
| `AI_API_KEY` |  | genérica deprecated (fallback) |

**Prioridade de chave por requisição:** `body.api_key` > `header X-AI-API-Key` > `env <PROVIDER>_API_KEY` > `env AI_API_KEY` > dummy `sk-test` (só em testes).

## Endpoints

### `GET /health`
```json
{"status":"ok","version":"1.0.0"}
```

### `GET /api/providers`
```json
{
  "providers": ["openai","anthropic","gemini"],
  "default": "openai",
  "default_models": {"openai":"gpt-4o-mini","anthropic":"claude-3-5-sonnet-latest","gemini":"gemini-2.0-flash"},
  "available_models": {
    "openai": ["gpt-4o-mini","gpt-4o","gpt-4.1-mini","gpt-4.1","o1-mini","o3-mini"],
    "anthropic": ["claude-3-5-sonnet-latest","claude-3-5-haiku-latest","claude-3-opus-latest","claude-3-haiku-20240307"],
    "gemini": ["gemini-2.0-flash","gemini-2.0-flash-exp","gemini-1.5-pro","gemini-1.5-flash","gemini-1.5-flash-8b"]
  }
}
```
Frontend consome este endpoint para popular os `<select>` de modelo **sem texto livre** (apenas modelos da lista; `422` se fora da lista).

### `POST /api/scrape`

Body:
```json
{
  "url": "https://example.com",
  "prompt": "Extraia produtos com nome e preço em JSON",
  "provider": "anthropic",
  "model": "claude-3-5-sonnet-latest",
  "api_key": "sk-ant-...",
  "max_tokens": 1024,
  "temperature": 0.2
}
```

Resposta:
```json
{
  "data": "{\"produtos\": [{\"nome\": \"Caneta\", \"preco\": \"10,00\"}]}",
  "provider": "anthropic",
  "model": "claude-3-5-sonnet-latest"
}
```

Cabeçalho alternativo para chave:
```
X-AI-API-Key: sk-ant-...
```

Erros: `422` provider/modelo inválido (modelo fora da lista por provider), `401` chave ausente/inválida, `429` rate limit, `502` erro do provedor.

### cURL

```bash
# OpenAI via .env
curl -X POST http://localhost:8000/api/scrape \
  -H "Content-Type: application/json" \
  -d '{"url":"https://example.com","prompt":"Extraia o título em JSON"}'

# Anthropic com chave do usuário
curl -X POST http://localhost:8000/api/scrape \
  -H "Content-Type: application/json" \
  -d '{"url":"https://books.toscrape.com","prompt":"Extraia livros em JSON","provider":"anthropic","api_key":"sk-ant-..."}'

# Gemini via header
curl -X POST http://localhost:8000/api/scrape \
  -H "Content-Type: application/json" \
  -H "X-AI-API-Key: AIza..." \
  -d '{"url":"https://example.com","prompt":"Extraia em JSON","provider":"gemini"}'

# Listar provedores
curl http://localhost:8000/api/providers
```

## Frontend

Abra `frontend/index.html` no navegador (ou `python -m http.server` na raiz).

Formulário contém: URL, prompt, **seletor de provider (obrigatório)**, **seletor de modelo (obrigatório, sem texto livre — lista por provider via `/api/providers`)**, **campo Sua API Key (obrigatório, password, não persistida)**, max_tokens/temperature, e exibição do JSON retornado.

Playwright roda em **modo silencioso headless** com stealth: `bypass_csp`, `user-agent` do `.env`, `viewport 1920x1080`, `locale pt-BR`, `args --disable-blink-features=AutomationControlled` e `add_init_script` que esconde `navigator.webdriver`, remove `script/style/iframe` e detecta/aguarde challenge Cloudflare/captcha.

## Testes

```bash
pytest -v
# ou com coverage
pytest --tb=short
```

35 testes cobrem: init/factory, `_build_client`, `get_data` com mocks por provider, stripping de cercas markdown (Gemini), validação de chave e header.

## Dependências

`pyproject.toml` e `requirements.txt` alinhados:

- API: `fastapi`, `uvicorn[standard]`, `python-dotenv`, `pydantic-settings`
- IA: `openai>=1.30`, `anthropic>=0.30`, `google-generativeai>=0.8`
- Scraping: `scrapegraphai`, `httpx`, `beautifulsoup4`, `lxml`, `playwright`, `nest-asyncio`
- Dev: `pytest`, `pytest-asyncio`, `ruff`, `httpx` (TestClient)

Instale browsers após `pip install`:

```bash
playwright install chromium
# opcional: playwright install --with-deps chromium
```

## Modelos

| Provedor | Default | Disponíveis (select, sem texto livre) |
|----------|---------|----------------------------------------|
| openai | `gpt-4o-mini` | `gpt-4o-mini`, `gpt-4o`, `gpt-4.1-mini`, `gpt-4.1`, `o1-mini`, `o3-mini` |
| anthropic | `claude-3-5-sonnet-latest` | `claude-3-5-sonnet-latest`, `claude-3-5-haiku-latest`, `claude-3-opus-latest`, `claude-3-haiku-20240307` |
| gemini | `gemini-2.0-flash` | `gemini-2.0-flash`, `gemini-2.0-flash-exp`, `gemini-1.5-pro`, `gemini-1.5-flash`, `gemini-1.5-flash-8b` |

`model` deve ser um dos disponíveis para o `provider` escolhido (`422` caso contrário). Gemini usa `max_output_tokens` internamente mapeado de `max_tokens`.
