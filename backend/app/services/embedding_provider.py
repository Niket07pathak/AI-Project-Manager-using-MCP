import os
import requests
from dotenv import load_dotenv

load_dotenv()

class EmbeddingProvider:
    def __init__(self):
        self.provider = os.getenv("EMBEDDING_PROVIDER", "local")
        self.api_url = os.getenv("EMBEDDING_API_URL", "http://localhost:8001")
        self.model = os.getenv("EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5")

    def embed(self, text: str) -> list[float]:
        url = f"{self.api_url}/embed"
        payload = {"text": text}

        response = requests.post(url, json=payload, timeout=600)
        response.raise_for_status()
        data = response.json()

        return data["embedding"]
    def health(self):
        url = f"{self.api_url}/health"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    
embedding_provider = EmbeddingProvider()