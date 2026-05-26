import os
import logging
import requests
from dotenv import load_dotenv

from backend.app.services.errors import ServiceError

load_dotenv()
logger = logging.getLogger(__name__)


class LLMProvider:
    def __init__(self):
        self.base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.model = os.getenv("OLLAMA_MODEL", "qwen2.5-coder:14b")
        self.provider = "ollama"

    def generate(self, prompt: str, num_predict: int = 800) -> str:
        url = f"{self.base_url}/api/generate"

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.2, "num_predict": num_predict},
        }

        try:
            response = requests.post(url, json=payload, timeout=120)
            response.raise_for_status()
            data = response.json()
        except requests.Timeout as exc:
            logger.warning("Ollama request timed out for model %s", self.model)
            raise ServiceError(
                "TIMEOUT",
                "ollama",
                "Ollama timed out while generating tasks. Please try again.",
            ) from exc
        except requests.ConnectionError as exc:
            logger.warning("Ollama connection failed")
            raise ServiceError(
                "SERVICE_UNAVAILABLE",
                "ollama",
                "Ollama is unavailable. Please start Ollama and try again.",
            ) from exc
        except requests.HTTPError as exc:
            logger.warning("Ollama returned HTTP error: %s", exc)
            raise ServiceError(
                "BAD_RESPONSE",
                "ollama",
                "Ollama returned an error while generating tasks.",
            ) from exc
        except ValueError as exc:
            logger.warning("Ollama returned invalid JSON")
            raise ServiceError(
                "INVALID_RESPONSE",
                "ollama",
                "Ollama returned an invalid response.",
            ) from exc

        generated = data.get("response")
        if not isinstance(generated, str):
            logger.warning("Ollama response missing response field")
            raise ServiceError(
                "INVALID_RESPONSE",
                "ollama",
                "Ollama returned an invalid response.",
            )

        return generated


llm_provider = LLMProvider()
