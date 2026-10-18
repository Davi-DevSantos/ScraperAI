# =============================================================
#                           AIScraper 
# =============================================================
FROM mcr.microsoft.com/playwright/python:v1.63.0-noble


ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app

WORKDIR /app


COPY pyproject.toml README.md ./
COPY app ./app


RUN pip install --no-cache-dir . \
    && playwright install --with-deps chromium


COPY frontend ./frontend

EXPOSE 8000


CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
