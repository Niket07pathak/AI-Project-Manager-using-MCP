import asyncio
import json
import os
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from backend.app.services.errors import error_response

PROJECT_ROOT = Path(__file__).resolve().parents[3]


class MCPTaskClient:
    def __init__(self):
        self.server_params = StdioServerParameters(
            command=sys.executable,
            args=[str(PROJECT_ROOT / "mcp_servers" / "task_server.py")],
            env=os.environ.copy(),
        )

    async def _call_tool_async(self, tool_name: str, arguments: dict) -> dict:
        try:
            async with stdio_client(self.server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()

                    result = await asyncio.wait_for(
                        session.call_tool(tool_name, arguments),
                        timeout=90,
                    )

                    if hasattr(result, "structured_content") and result.structured_content:
                        return result.structured_content

                    if hasattr(result, "content") and result.content:
                        content = result.content[0]

                        if hasattr(content, "text") and content.text:
                            try:
                                return json.loads(content.text)
                            except json.JSONDecodeError:
                                return {"error": content.text}

                    return {"success": True}
        except asyncio.TimeoutError:
            return error_response(
                "TIMEOUT",
                "task_mcp_server",
                "Task MCP server timed out.",
            )
        except Exception as exc:
            return error_response(
                "MCP_TOOL_FAILURE",
                "task_mcp_server",
                "Task MCP server failed while executing a tool.",
                details=str(exc),
            )

    def call_tool(self, tool_name: str, arguments: dict) -> dict:
        return asyncio.run(self._call_tool_async(tool_name, arguments))

    def list_project_tasks(
        self,
        project_id: int,
        user_id: str | None = None,
        auth_token: str | None = None,
    ) -> dict:
        return self.call_tool(
            "list_project_tasks",
            {
                "project_id": project_id,
                "user_id": user_id,
            },
        )

    def create_task(
        self,
        project_id: int,
        title: str,
        description: str,
        priority: str = "medium",
        user_id: str | None = None,
        auth_token: str | None = None,
    ) -> dict:
        return self.call_tool(
            "create_task",
            {
                "user_id": user_id,
                "project_id": project_id,
                "title": title,
                "description": description,
                "priority": priority,
            },
        )

    def edit_task(
        self,
        task_id: int,
        title: str | None = None,
        description: str | None = None,
        priority: str | None = None,
        user_id: str | None = None,
        auth_token: str | None = None,
    ) -> dict:
        return self.call_tool(
            "edit_task",
            {
                "task_id": task_id,
                "title": title,
                "description": description,
                "priority": priority,
                "user_id": user_id,
            },
        )

    def approve_task(
        self,
        task_id: int,
        user_id: str | None = None,
        auth_token: str | None = None,
    ) -> dict:
        return self.call_tool(
            "approve_task",
            {
                "task_id": task_id,
                "user_id": user_id,
            },
        )

    def reject_task(
        self,
        task_id: int,
        user_id: str | None = None,
        auth_token: str | None = None,
    ) -> dict:
        return self.call_tool(
            "reject_task",
            {
                "task_id": task_id,
                "user_id": user_id,
            },
        )

    def create_audit_log(
        self,
        project_id: int | None,
        user_id: str,
        action: str,
        tool_name: str | None = None,
        input_data: str | None = None,
        output_data: str | None = None,
        status: str = "success",
        auth_token: str | None = None,
    ) -> dict:
        serialized_input = (
            input_data if isinstance(input_data, str) else json.dumps(input_data)
        )
        serialized_output = (
            output_data if isinstance(output_data, str) else json.dumps(output_data)
        )

        return self.call_tool(
            "create_audit_log",
            {
                "project_id": project_id,
                "user_id": user_id,
                "action": action,
                "tool_name": tool_name,
                "input_data": serialized_input,
                "output_data": serialized_output,
                "status": status,
            },
        )

mcp_task_client = MCPTaskClient()
