import json
from backend.app.services.llm_provider import llm_provider
from backend.app.services.qdrant_provider import qdrant_provider
from backend.app.services.embedding_provider import embedding_provider
import re


def parse_llm_json(response: str):
    response = response.strip()

    # Remove markdown code fence if present
    response = re.sub(r"^```json\s*", "", response)
    response = re.sub(r"^```\s*", "", response)
    response = re.sub(r"\s*```$", "", response)

    return json.loads(response)


def retrieve_project_context(project_id: int, query: str, top_k: int = 5) -> list[dict]:
    query_embedding = embedding_provider.embed(query)

    results = qdrant_provider.search_chunks(
        query_embedding=query_embedding,
        project_id=project_id,
        top_k=top_k,
    )

    return [
        {
            "score": result.score,
            "chunk_id": result.payload.get("chunk_id"),
            "document_id": result.payload.get("document_id"),
            "chunk_index": result.payload.get("chunk_index"),
            "content": result.payload.get("content"),
        }
        for result in results
    ]


def generate_tasks_from_context(
    project_id: int, context_chunks: list[dict]
) -> list[dict]:
    context_text = "\n\n".join(
        [chunk["content"] for chunk in context_chunks if chunk.get("content")]
    )

    prompt = f"""
You are an AI Project Manager.

Based on the project document context below, generate  4 to 6 implementation tasks.

Return ONLY valid JSON.
Do not include markdown.
Do not include explanation.
Make sure the JSON array is complete and properly closed.


JSON format:
[
  {{
    "title": "Short task title",
    "description": "Clear implementation description",
    "priority": "low | medium | high"
  }}
]

Project ID: {project_id}

Context:
{context_text}
"""

    response = llm_provider.generate(prompt, num_predict=800)

    try:
        tasks = parse_llm_json(response)
    except json.JSONDecodeError:
        raise ValueError(f"LLM did not return valid JSON: {response}")

    return tasks


def analyze_project(project_id: int) -> dict:
    context_chunks = retrieve_project_context(
        project_id=project_id,
        query="project requirements features implementation tasks user stories",
        top_k=8,
    )

    tasks = generate_tasks_from_context(
        project_id=project_id,
        context_chunks=context_chunks,
    )

    return {
        "project_id": project_id,
        "chunks_used": len(context_chunks),
        "tasks": tasks,
    }
