import os
import sys
from pathlib import Path
import sys

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, ".."))

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
    
import requests
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
import json
import logging
from typing import Any
from backend.app.services.errors import error_response

load_dotenv()
logger = logging.getLogger(__name__)

BACKEND_API_URL = os.getenv("BACKEND_API_URL", "http://localhost:8000")
INTERNAL_API_KEY = os.getenv("INTERNAL_API_KEY")

mcp = FastMCP("task-manager-server")


def internal_headers() -> dict:
    if not INTERNAL_API_KEY:
        raise RuntimeError("INTERNAL_API_KEY is not configured.")
    return {"X-Internal-API-Key": INTERNAL_API_KEY}


def response_json(response: requests.Response, service: str = "task") -> dict:
    try:
        return response.json()
    except ValueError:
        logger.warning("%s backend returned invalid JSON", service)
        return error_response(
            "INVALID_RESPONSE",
            service,
            "Backend returned an invalid response.",
        )


@mcp.tool()
def list_project_tasks(
    project_id: int,
    user_id: str | None = None,
) -> dict:
    """
    List all tasks for a project.
    """
    url = f"{BACKEND_API_URL}/project/{project_id}/tasks"

    try:
        response = requests.get(
            url,
            params={"user_id": user_id},
            headers=internal_headers(),
            timeout=30,
        )
        response.raise_for_status()
    except RuntimeError as exc:
        logger.warning("Task MCP internal auth configuration error: %s", exc)
        return error_response("CONFIGURATION_ERROR", "task", "Internal API key is not configured.")
    except requests.RequestException as exc:
        logger.warning("Task MCP list tasks failed for project %s: %s", project_id, exc)
        return error_response("BAD_RESPONSE", "task", "Could not list project tasks.")

    data = response_json(response)
    if isinstance(data, dict) and data.get("success") is False:
        return data

    return {
        "project_id": project_id,
        "tasks": data,
    }


@mcp.tool()
def create_task(
    project_id: int,
    title: str,
    description: str,
    priority: str = "medium",
    user_id: str | None = None,
) -> dict:
    """
    Create a new pending approval task for a project.
    """
    url = f"{BACKEND_API_URL}/tasks"

    payload = {
        "user_id": user_id,
        "project_id": project_id,
        "title": title,
        "description": description,
        "priority": priority,
        "status": "pending_approval",
        "approved": False,
    }

    try:
        response = requests.post(
            url,
            json=payload,
            headers=internal_headers(),
            timeout=30,
        )
        response.raise_for_status()
    except RuntimeError as exc:
        logger.warning("Task MCP internal auth configuration error: %s", exc)
        return error_response("CONFIGURATION_ERROR", "task", "Internal API key is not configured.")
    except requests.RequestException as exc:
        logger.warning("Task MCP create task failed for project %s: %s", project_id, exc)
        return error_response("BAD_RESPONSE", "task", "Could not create task.")

    return response_json(response)


@mcp.tool()
def edit_task(
    task_id: int,
    title: str | None = None,
    description: str | None = None,
    priority: str | None = None,
    user_id: str | None = None,
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

    try:
        response = requests.patch(
            url,
            params={"user_id": user_id},
            json=payload,
            headers=internal_headers(),
            timeout=30,
        )
        response.raise_for_status()
    except RuntimeError as exc:
        logger.warning("Task MCP internal auth configuration error: %s", exc)
        return error_response("CONFIGURATION_ERROR", "task", "Internal API key is not configured.")
    except requests.RequestException as exc:
        logger.warning("Task MCP edit task failed for task %s: %s", task_id, exc)
        return error_response("BAD_RESPONSE", "task", "Could not edit task.")

    return response_json(response)


@mcp.tool()
def approve_task(
    task_id: int,
    user_id: str | None = None,
) -> dict:
    """
    Approve a task so it becomes eligible for GitHub issue creation.
    """
    url = f"{BACKEND_API_URL}/tasks/{task_id}/approve"

    try:
        response = requests.patch(
            url,
            params={"user_id": user_id},
            headers=internal_headers(),
            timeout=30,
        )
        response.raise_for_status()
    except RuntimeError as exc:
        logger.warning("Task MCP internal auth configuration error: %s", exc)
        return error_response("CONFIGURATION_ERROR", "task", "Internal API key is not configured.")
    except requests.RequestException as exc:
        logger.warning("Task MCP approve task failed for task %s: %s", task_id, exc)
        return error_response("BAD_RESPONSE", "task", "Could not approve task.")

    return response_json(response)


@mcp.tool()
def reject_task(
    task_id: int,
    user_id: str | None = None,
) -> dict:
    """
    Reject a generated task.
    """
    url = f"{BACKEND_API_URL}/tasks/{task_id}/reject"

    try:
        response = requests.patch(
            url,
            params={"user_id": user_id},
            headers=internal_headers(),
            timeout=30,
        )
        response.raise_for_status()
    except RuntimeError as exc:
        logger.warning("Task MCP internal auth configuration error: %s", exc)
        return error_response("CONFIGURATION_ERROR", "task", "Internal API key is not configured.")
    except requests.RequestException as exc:
        logger.warning("Task MCP reject task failed for task %s: %s", task_id, exc)
        return error_response("BAD_RESPONSE", "task", "Could not reject task.")

    return response_json(response)


@mcp.tool()
def create_audit_log(
    project_id: int | None,
    user_id: str,
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
        "user_id": user_id,
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

    try:
        response = requests.post(
            url,
            json=payload,
            headers=internal_headers(),
            timeout=30,
        )
        response.raise_for_status()
    except RuntimeError as exc:
        logger.warning("Task MCP internal auth configuration error: %s", exc)
        return error_response("CONFIGURATION_ERROR", "task", "Internal API key is not configured.")
    except requests.RequestException as exc:
        logger.warning("Task MCP create audit log failed for project %s: %s", project_id, exc)
        return error_response("BAD_RESPONSE", "task", "Could not write audit log.")

    return response_json(response)


if __name__ == "__main__":
    mcp.run()
