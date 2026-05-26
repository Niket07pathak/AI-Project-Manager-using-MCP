FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY requirements.embedding.docker.txt .

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.embedding.docker.txt
        
COPY embedding_api ./embedding_api

EXPOSE 8001

CMD ["uvicorn", "embedding_api.main:app", "--host", "0.0.0.0", "--port", "8001"]