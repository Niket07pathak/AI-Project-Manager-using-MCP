import os
import logging
import requests
from dotenv import load_dotenv

from backend.app.services.errors import ServiceError

load_dotenv()
logger = logging.getLogger(__name__)

class EmbeddingProvider:
    def __init__(self):
        self.provider = os.getenv("EMBEDDING_PROVIDER", "local")
        self.api_url = os.getenv("EMBEDDING_API_URL", "http://localhost:8001")
        self.model = os.getenv("EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5")

    def embed(self, text: str) -> list[float]:
        url = f"{self.api_url}/embed"
        payload = {"text": text}

        try:
            response = requests.post(url, json=payload, timeout=60)
            response.raise_for_status()
            data = response.json()
        except requests.Timeout as exc:
            logger.warning("Embedding API timed out at %s", url)
            raise ServiceError(
                "TIMEOUT",
                "embedding_api",
                "Embedding service timed out. Please try again.",
            ) from exc
        except requests.ConnectionError as exc:
            logger.warning("Embedding API unavailable at %s", self.api_url)
            raise ServiceError(
                "SERVICE_UNAVAILABLE",
                "embedding_api",
                "Embedding service is unavailable. Please start it and try again.",
            ) from exc
        except requests.HTTPError as exc:
            logger.warning("Embedding API returned HTTP error: %s", exc)
            raise ServiceError(
                "BAD_RESPONSE",
                "embedding_api",
                "Embedding service returned an error.",
            ) from exc
        except ValueError as exc:
            logger.warning("Embedding API returned invalid JSON")
            raise ServiceError(
                "INVALID_RESPONSE",
                "embedding_api",
                "Embedding service returned an invalid response.",
            ) from exc

        embedding = data.get("embedding")
        if not isinstance(embedding, list) or not embedding:
            logger.warning("Embedding API returned empty or invalid embedding: %s", data)
            raise ServiceError(
                "INVALID_RESPONSE",
                "embedding_api",
                "Embedding service returned an empty embedding.",
            )

        return embedding
    def health(self):
        url = f"{self.api_url}/health"
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as exc:
            logger.warning("Embedding API health check failed: %s", exc)
            raise ServiceError(
                "SERVICE_UNAVAILABLE",
                "embedding_api",
                "Embedding service health check failed.",
            ) from exc
    
embedding_provider = EmbeddingProvider()
