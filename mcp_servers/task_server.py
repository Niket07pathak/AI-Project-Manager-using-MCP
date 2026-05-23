import os
import requests
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
import json
from typing import Any

load_dotenv()

BACKEND_API_URL = os.getenv("BACKEND_API_URL", "http://localhost:8000")

mcp = FastMCP("task-manager-server")


@mcp.tool()
def list_project_tasks(project_id: int) -> dict:
    """
    List all tasks for a project.
    """
    url = f"{BACKEND_API_URL}/project/{project_id}/tasks"

    response = requests.get(url, timeout=30)
    response.raise_for_status()

    return {
        "project_id": project_id,
        "tasks": response.json(),
    }


@mcp.tool()
def create_task(
    project_id: int,
    title: str,
    description: str,
    priority: str = "medium",
) -> dict:
    """
    Create a new pending approval task for a project.
    """
    url = f"{BACKEND_API_URL}/tasks"

    payload = {
        "project_id": project_id,
        "title": title,
        "description": description,
        "priority": priority,
        "status": "pending_approval",
        "approved": False,
    }

    response = requests.post(url, json=payload, timeout=30)
    response.raise_for_status()

    return response.json()


@mcp.tool()
def edit_task(
    task_id: int,
    title: str | None = None,
    description: str | None = None,
    priority: str | None = None,
) -> dict:
    """
    Edit an existing task.
    """
    url = f"{BACKEND_API_URL}/tasks/{task_id}/edit"

    payload = {
        "title": title,
        "description": description,
        "priority": priority,
    }

    response = requests.patch(url, json=payload, timeout=30)
    response.raise_for_status()

    return response.json()


@mcp.tool()
def approve_task(task_id: int) -> dict:
    """
    Approve a task so it becomes eligible for GitHub issue creation.
    """
    url = f"{BACKEND_API_URL}/tasks/{task_id}/approve"

    response = requests.patch(url, timeout=30)
    response.raise_for_status()

    return response.json()


@mcp.tool()
def reject_task(task_id: int) -> dict:
    """
    Reject a generated task.
    """
    url = f"{BACKEND_API_URL}/tasks/{task_id}/reject"

    response = requests.patch(url, timeout=30)
    response.raise_for_status()

    return response.json()


@mcp.tool()
def create_audit_log(
    project_id: int | None,
    action: str,
    tool_name: str | None = None,
    input_data: Any = None,
    output_data: Any = None,
    status: str = "success",
) -> dict:
    """
    Create an audit log entry through the backend.
    """
    url = f"{BACKEND_API_URL}/audit-logs"

    payload = {
        "project_id": project_id,
        "action": action,
        "tool_name": tool_name,
        "input_data": (
            input_data if isinstance(input_data, str) else json.dumps(input_data)
        ),
        "output_data": (
            output_data if isinstance(output_data, str) else json.dumps(output_data)
        ),
        "status": status,
    }

    response = requests.post(url, json=payload, timeout=30)
    response.raise_for_status()

    return response.json()


if __name__ == "__main__":
    mcp.run()
