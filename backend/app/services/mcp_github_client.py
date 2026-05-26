import asyncio
import json
import os
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from backend.app.services.errors import error_response

PROJECT_ROOT = Path(__file__).resolve().parents[3]


class MCPGitHubClient:
    def __init__(self):
        self.server_params = StdioServerParameters(
            command=sys.executable,
            args=[str(PROJECT_ROOT / "mcp_servers" / "github_server.py")],
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
            return error_response("TIMEOUT", "github_mcp_server", "GitHub MCP server timed out.")
        except Exception as exc:
            return error_response(
                "MCP_TOOL_FAILURE",
                "github_mcp_server",
                "GitHub MCP server failed while executing a tool.",
                details=str(exc),
            )

    def call_tool(self, tool_name: str, arguments: dict) -> dict:
        return asyncio.run(self._call_tool_async(tool_name, arguments))

    def create_github_issue(
        self,
        repo_owner: str,
        repo_name: str,
        title: str,
        body: str,
        labels: list[str] | None = None,
    ) -> dict:
        return self.call_tool(
            "create_github_issue",
            {
                "repo_owner": repo_owner,
                "repo_name": repo_name,
                "title": title,
                "body": body,
                "labels": labels or [],
            },
        )

    def list_repo_issues(self, state: str = "open") -> dict:
        return self.call_tool(
            "list_repo_issues",
            {
                "state": state,
            },
        )

    def comment_on_issue(self, issue_number: int, comment: str) -> dict:
        return self.call_tool(
            "comment_on_issue",
            {
                "issue_number": issue_number,
                "comment": comment,
            },
        )


mcp_github_client = MCPGitHubClient()
