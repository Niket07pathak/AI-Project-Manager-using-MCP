import json
import re
from typing import Any, TypedDict

from langgraph.graph import StateGraph, END
from sqlalchemy.orm import Session

from backend.app import schemas, crud
from backend.app.services.llm_provider import llm_provider
from backend.app.services.mcp_rag_client import mcp_rag_client
from backend.app.services.mcp_task_client import mcp_task_client


class ProjectAnalyzerState(TypedDict):
    project_id: int
    db: Any
    query: str
    context_chunks: list[dict]
    raw_llm_response: str | None
    tasks: list[dict]
    created_task_ids: list[int]
    chunks_used: int
    retry_count: int
    error: str | None


def parse_llm_json(response: str) -> list[dict]:
    try:
        return json.loads(response)
    except json.JSONDecodeError:
        pass

    match = re.search(r"\[.*\]", response, re.DOTALL)
    if not match:
        raise ValueError("No JSON array found in LLM response")

    return json.loads(match.group(0))


def retrieve_context_node(state: ProjectAnalyzerState) -> ProjectAnalyzerState:
    result = mcp_rag_client.search_project_docs(
        project_id=state["project_id"],
        query=state["query"],
        top_k=8,
    )

    context_chunks = result.get("results", [])

    state["context_chunks"] = context_chunks
    state["chunks_used"] = len(context_chunks)

    return state


def generate_tasks_node(state: ProjectAnalyzerState) -> ProjectAnalyzerState:
    context_text = "\n\n".join(
        chunk["content"] for chunk in state["context_chunks"] if chunk.get("content")
    )

    prompt = f"""
You are an AI Project Manager.

Based on the project document context below, generate 4 to 6 implementation tasks maximum.

Return ONLY valid JSON.
Do not include markdown.
Do not include explanation.
Make sure the JSON array is complete and properly closed.

Each task must have:
- title
- description
- priority

Allowed priority values:
low, medium, high

JSON format:
[
  {{
    "title": "Short task title",
    "description": "Clear implementation description",
    "priority": "medium"
  }}
]

Project ID: {state["project_id"]}

Context:
{context_text}
"""

    response = llm_provider.generate(prompt, num_predict=1000)
    state["raw_llm_response"] = response

    return state


def validate_tasks_node(state: ProjectAnalyzerState) -> ProjectAnalyzerState:
    try:
        tasks = parse_llm_json(state["raw_llm_response"] or "")

        cleaned_tasks = []

        for task in tasks:
            title = task.get("title")
            description = task.get("description")
            priority = task.get("priority", "medium")

            if not title or not description:
                continue

            if priority not in ["low", "medium", "high"]:
                priority = "medium"

            cleaned_tasks.append(
                {
                    "title": title.strip(),
                    "description": description.strip(),
                    "priority": priority,
                }
            )

        if not cleaned_tasks:
            raise ValueError("No valid tasks found after validation")

        state["tasks"] = cleaned_tasks
        state["error"] = None

    except Exception as e:
        state["tasks"] = []
        state["error"] = str(e)
        state["retry_count"] += 1

    return state


def should_retry_or_save(state: ProjectAnalyzerState) -> str:
    if state["tasks"]:
        return "save_tasks"

    if state["retry_count"] < 2:
        return "generate_tasks"

    return "write_failure_audit"


def save_tasks_node(state: ProjectAnalyzerState) -> ProjectAnalyzerState:
    created_task_ids = []

    for task in state["tasks"]:
        created_task = mcp_task_client.create_task(
            project_id=state["project_id"],
            title=task["title"],
            description=task["description"],
            priority=task["priority"],
        )

        created_task_ids.append(created_task["id"])

    state["created_task_ids"] = created_task_ids

    return state


def write_success_audit_node(state: ProjectAnalyzerState) -> ProjectAnalyzerState:
    audit_result = mcp_task_client.create_audit_log(
        project_id=state["project_id"],
        action="project_analysis_completed",
        tool_name="langgraph_project_analyzer",
        input_data=json.dumps(
            {
                "query": state["query"],
                "chunks_used": state["chunks_used"],
            }
        ),
        output_data=json.dumps(
            {
                "tasks_created": len(state["created_task_ids"]),
                "task_ids": state["created_task_ids"],
            }
        ),
        status="success",
    )

    print("Writing success audit for project:", state["project_id"])
    print("Audit result:", audit_result)

    return state


def write_failure_audit_node(state: ProjectAnalyzerState) -> ProjectAnalyzerState:
    mcp_task_client.create_audit_log(
        project_id=state["project_id"],
        action="project_analysis_failed",
        tool_name="langgraph_project_analyzer",
        input_data=json.dumps(
            {
                "query": state["query"],
                "chunks_used": state["chunks_used"],
                "retry_count": state["retry_count"],
            }
        ),
        output_data=json.dumps(
            {
                "error": state["error"],
                "raw_llm_response": state["raw_llm_response"],
            }
        ),
        status="failed",
    )

    return state


def build_project_analyzer_graph():
    graph = StateGraph(ProjectAnalyzerState)

    graph.add_node("retrieve_context", retrieve_context_node)
    graph.add_node("generate_tasks", generate_tasks_node)
    graph.add_node("validate_tasks", validate_tasks_node)
    graph.add_node("save_tasks", save_tasks_node)
    graph.add_node("write_success_audit", write_success_audit_node)
    graph.add_node("write_failure_audit", write_failure_audit_node)

    graph.set_entry_point("retrieve_context")

    graph.add_edge("retrieve_context", "generate_tasks")
    graph.add_edge("generate_tasks", "validate_tasks")

    graph.add_conditional_edges(
        "validate_tasks",
        should_retry_or_save,
        {
            "generate_tasks": "generate_tasks",
            "save_tasks": "save_tasks",
            "write_failure_audit": "write_failure_audit",
        },
    )

    graph.add_edge("save_tasks", "write_success_audit")
    graph.add_edge("write_success_audit", END)
    graph.add_edge("write_failure_audit", END)

    return graph.compile()


project_analyzer_graph = build_project_analyzer_graph()


def analyze_project_with_langgraph(project_id: int, db: Session) -> dict:
    initial_state: ProjectAnalyzerState = {
        "project_id": project_id,
        "db": db,
        "query": "project requirements features implementation tasks user stories approval workflow integrations",
        "context_chunks": [],
        "raw_llm_response": None,
        "tasks": [],
        "created_task_ids": [],
        "chunks_used": 0,
        "retry_count": 0,
        "error": None,
    }

    final_state = project_analyzer_graph.invoke(initial_state)

    if final_state.get("error") and not final_state.get("created_task_ids"):
        raise ValueError(final_state["error"])

    return {
        "project_id": project_id,
        "chunks_used": final_state["chunks_used"],
        "tasks_created": len(final_state["created_task_ids"]),
        "task_ids": final_state["created_task_ids"],
    }
