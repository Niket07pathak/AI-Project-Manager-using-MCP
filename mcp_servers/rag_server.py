import os
import sys
from pathlib import Path
import sys

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, ".."))

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import logging
import requests
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from backend.app.services.errors import error_response

load_dotenv()
logger = logging.getLogger(__name__)

BACKEND_API_URL = os.getenv("BACKEND_API_URL", "http://localhost:8000")
INTERNAL_API_KEY = os.getenv("INTERNAL_API_KEY")

mcp = FastMCP("rag-server")


def internal_headers() -> dict:
    if not INTERNAL_API_KEY:
        raise RuntimeError("INTERNAL_API_KEY is not configured.")
    return {"X-Internal-API-Key": INTERNAL_API_KEY}


def response_json(response: requests.Response) -> dict:
    try:
        return response.json()
    except ValueError:
        logger.warning("RAG backend returned invalid JSON")
        return error_response(
            "INVALID_RESPONSE",
            "rag",
            "Backend returned an invalid response.",
        )


@mcp.tool()
def search_project_docs(
    project_id: int,
    query: str,
    top_k: int = 5,
    user_id: str | None = None,
) -> dict:
    url = f"{BACKEND_API_URL}/projects/{project_id}/search"

    payload = {
        "query": query,
        "top_k": top_k,
        "user_id": user_id,
    }

    try:
        response = requests.post(
            url,
            json=payload,
            headers=internal_headers(),
            timeout=60,
        )
        response.raise_for_status()
    except RuntimeError as exc:
        logger.warning("RAG internal auth configuration error: %s", exc)
        return error_response("CONFIGURATION_ERROR", "rag", "Internal API key is not configured.")
    except requests.RequestException as exc:
        logger.warning("RAG backend search failed for project %s: %s", project_id, exc)
        return error_response(
            "BAD_RESPONSE",
            "rag",
            "Project document search failed.",
        )

    return response_json(response)

@mcp.tool()
def retrieve_chunks(
    project_id: int,
    query: str,
    top_k: int = 5,
    user_id: str | None = None,
) -> list[dict]:
    result = search_project_docs(
        project_id=project_id,
        query=query,
        top_k=top_k,
        user_id=user_id,
    )

    return result.get("results", [])


@mcp.tool()
def read_document(
    document_id: int,
    user_id: str | None = None,
) -> dict:
    """
    Read document metadata and stored chunks from the backend.
    """
    document_url = f"{BACKEND_API_URL}/documents/{document_id}"
    chunks_url = f"{BACKEND_API_URL}/documents/{document_id}/chunks"

    try:
        document_response = requests.get(
            document_url,
            params={"user_id": user_id},
            headers=internal_headers(),
            timeout=30,
        )
        document_response.raise_for_status()

        chunks_response = requests.get(
            chunks_url,
            params={"user_id": user_id},
            headers=internal_headers(),
            timeout=30,
        )
        chunks_response.raise_for_status()
    except RuntimeError as exc:
        logger.warning("RAG internal auth configuration error: %s", exc)
        return error_response("CONFIGURATION_ERROR", "rag", "Internal API key is not configured.")
    except requests.RequestException as exc:
        logger.warning("RAG read document failed for document %s: %s", document_id, exc)
        return error_response("BAD_RESPONSE", "rag", "Could not read document context.")

    return {
        "document": response_json(document_response),
        "chunks": response_json(chunks_response),
    }


if __name__ == "__main__":
    mcp.run()
