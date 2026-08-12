"""Configurações da aplicação (pydantic-settings).

Lê as variáveis do arquivo .env e disponibiliza via objeto singleton,
ex.: `from app.core.config import settings`.
"""

# TODO: Criar classe Settings(BaseSettings) mapeando as variáveis do .env
# TODO: Expor instância única: settings = Settings()