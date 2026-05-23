import os
import requests
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

load_dotenv()

BACKEND_API_URL = os.getenv("BACKEND_API_URL", "http://localhost:8000")

mcp = FastMCP("rag-server")


@mcp.tool()
def search_project_docs(project_id: int, query: str, top_k: int = 5) -> dict:
    """
    Search project documents using semantic search.
    Returns top matching chunks from Qdrant through the FastAPI backend.
    """
    url = f"{BACKEND_API_URL}/projects/{project_id}/search"

    payload = {
        "query": query,
        "top_k": top_k,
    }

    response = requests.post(url, json=payload, timeout=60)
    response.raise_for_status()

    return response.json()


@mcp.tool()
def retrieve_chunks(project_id: int, query: str, top_k: int = 5) -> list[dict]:
    """
    Retrieve only the matching chunks for a project.
    """
    result = search_project_docs(
        project_id=project_id,
        query=query,
        top_k=top_k,
    )

    return result.get("results", [])


@mcp.tool()
def read_document(document_id: int) -> dict:
    """
    Read document metadata and stored chunks from the backend.
    """
    document_url = f"{BACKEND_API_URL}/documents/{document_id}"
    chunks_url = f"{BACKEND_API_URL}/documents/{document_id}/chunks"

    document_response = requests.get(document_url, timeout=30)
    document_response.raise_for_status()

    chunks_response = requests.get(chunks_url, timeout=30)
    chunks_response.raise_for_status()

    return {
        "document": document_response.json(),
        "chunks": chunks_response.json(),
    }


if __name__ == "__main__":
    mcp.run()