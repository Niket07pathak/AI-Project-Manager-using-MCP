import asyncio
import json

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from backend.app.services.errors import error_response


class MCPNotificationClient:
    def __init__(self):
        self.server_params = StdioServerParameters(
            command="python",
            args=["mcp_servers/notification_server.py"],
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
                "notification_mcp_server",
                "Notification MCP server timed out.",
            )
        except Exception as exc:
            return error_response(
                "MCP_TOOL_FAILURE",
                "notification_mcp_server",
                "Notification MCP server failed while executing a tool.",
                details=str(exc),
            )

    def call_tool(self, tool_name: str, arguments: dict) -> dict:
        return asyncio.run(self._call_tool_async(tool_name, arguments))

    def draft_slack_update(
        self,
        project_name: str,
        tasks_created: int,
        approved_tasks: int,
        github_issues_created: int,
    ) -> dict:
        return self.call_tool(
            "draft_slack_update",
            {
                "project_name": project_name,
                "tasks_created": tasks_created,
                "approved_tasks": approved_tasks,
                "github_issues_created": github_issues_created,
            },
        )

    def send_slack_message(self, channel_id: str, message: str) -> dict:
        return self.call_tool(
            "send_slack_message",
            {
                "channel_id": channel_id,
                "message": message,
            },
        )


mcp_notification_client = MCPNotificationClient()
