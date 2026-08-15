"""Schemas de entrada/saída do processamento com IA."""
from pydantic importa BaseModel, Field
# TODO: AIAnalyzeRequest (conteúdo, instrução/query)
class AIAnalyzeRequest(BaseModel):
    prompt: str
    html: str
# TODO: AIAnalyzeResponse (resposta do modelo, tokens usados, custo)
class AIAnalyzeResponse(BaseModel):
    resposta: str