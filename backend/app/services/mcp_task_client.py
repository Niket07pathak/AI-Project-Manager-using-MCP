import asyncio
import json

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


class MCPTaskClient:
    def __init__(self):
        self.server_params = StdioServerParameters(
            command="python",
            args=["mcp_servers/task_server.py"],
        )

    async def _call_tool_async(self, tool_name: str, arguments: dict) -> dict:
        async with stdio_client(self.server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()

                result = await session.call_tool(tool_name, arguments)

                if hasattr(result, "structured_content") and result.structured_content:
                    return result.structured_content

                if hasattr(result, "content") and result.content:
                    content = result.content[0]

                    if hasattr(content, "text") and content.text:
                        try:
                            return json.loads(content.text)
                        except json.JSONDecodeError:
                            return {"text": content.text}

                return {"success": True}

    def call_tool(self, tool_name: str, arguments: dict) -> dict:
        return asyncio.run(self._call_tool_async(tool_name, arguments))

    def list_project_tasks(self, project_id: int) -> dict:
        return self.call_tool(
            "list_project_tasks",
            {
                "project_id": project_id,
            },
        )

    def create_task(
        self,
        project_id: int,
        title: str,
        description: str,
        priority: str = "medium",
    ) -> dict:
        return self.call_tool(
            "create_task",
            {
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
    ) -> dict:
        return self.call_tool(
            "edit_task",
            {
                "task_id": task_id,
                "title": title,
                "description": description,
                "priority": priority,
            },
        )

    def approve_task(self, task_id: int) -> dict:
        return self.call_tool(
            "approve_task",
            {
                "task_id": task_id,
            },
        )

    def reject_task(self, task_id: int) -> dict:
        return self.call_tool(
            "reject_task",
            {
                "task_id": task_id,
            },
        )

    def create_audit_log(
    self,
    project_id: int | None,
    action: str,
    tool_name: str | None = None,
    input_data: str | None = None,
    output_data: str | None = None,
    status: str = "success",
    ) -> dict:
        return self.call_tool(
            "create_audit_log",
            {
                "project_id": project_id,
                "action": action,
                "tool_name": tool_name,
                "input_data": input_data if isinstance(input_data, str) else json.dumps(input_data),
                "output_data": output_data if isinstance(output_data, str) else json.dumps(output_data),
                "status": status,
            },
        )

mcp_task_client = MCPTaskClient()