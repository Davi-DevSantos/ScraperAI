from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file = '.env',
        env_file_encoding = 'utf-8',
        extra = 'ignore',
    )

        # ===== API =====
    API_HOST: str = '0.0.0.0'
    API_PORT: int = 8000
    API_DEBUG: bool = True

    # ===== CORS (origens permitidas para o frontend) =====
    CORS_ORIGINS: list[str] = ["http://localhost:3000","http://127.0.0.1:3000"]

    # ===== IA =====
    # Chave da API do provedor de IA (OpenAI, Anthropic, etc.)
    AI_API_KEY: str = ''
    AI_PROVIDER: str = 'openai'
    AI_MODEL: str = 'gpt-4o-mini'
    AI_MAX_TOKENS: int = 2048
    AI_TEMPERATURE: float = 0.2

    # ===== Scraper =====
    # Timeout (segundos) para as requisições HTTP do scraper
    SCRAPER_TIMEOUT: int = 30
    # User-Agent usado nas requisições
    SCRAPER_USER_AGENT: str = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    # Número máximo de páginas por scrape
    SCRAPER_MAX_PAGES: int = 10

setting = Settings()