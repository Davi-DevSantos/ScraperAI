from pydantic import BaseModel, Field

class AIAnalyzeRequest(BaseModel):
    prompt: str = Field(description='The prompt user')
    html: str = Field(description='The html of site')  


class AIAnalyzeResponse(BaseModel):
    resposta: str