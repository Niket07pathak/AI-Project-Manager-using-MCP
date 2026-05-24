import asyncio
import json
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from backend.app.services.errors import error_response


class MCPRagClient:
    def __init__(self):
        self.server_params = StdioServerParameters(
            command="python",
            args=["mcp_servers/rag_server.py"],
        )

    async def search_project_docs_async(
        self,
        project_id: int,
        query: str,
        top_k: int = 5,
        user_id: str | None = None,
        auth_token: str | None = None,
    ) -> dict:
        try:
            async with stdio_client(self.server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()

                    result = await asyncio.wait_for(
                        session.call_tool(
                            "search_project_docs",
                            {
                                "project_id": project_id,
                                "query": query,
                                "top_k": top_k,
                                "user_id": user_id,
                            },
                        ),
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
            return error_response("TIMEOUT", "rag_mcp_server", "RAG MCP server timed out.")
        except Exception as exc:
            return error_response(
                "MCP_TOOL_FAILURE",
                "rag_mcp_server",
                "RAG MCP server failed while executing a tool.",
                details=str(exc),
            )

    def search_project_docs(
        self,
        project_id: int,
        query: str,
        top_k: int = 5,
        user_id: str | None = None,
        auth_token: str | None = None,
    ) -> dict:
        return asyncio.run(
            self.search_project_docs_async(
                project_id=project_id,
                query=query,
                top_k=top_k,
                user_id=user_id,
            )
        )

    def retrieve_chunks(
        self,
        project_id: int,
        query: str,
        top_k: int = 5,
        user_id: str | None = None,
        auth_token: str | None = None,
    ) -> dict:
        return asyncio.run(
            self._call_retrieve_chunks_async(
                project_id=project_id,
                query=query,
                top_k=top_k,
                user_id=user_id,
            )
        )

    async def _call_retrieve_chunks_async(
        self,
        project_id: int,
        query: str,
        top_k: int = 5,
        user_id: str | None = None,
        auth_token: str | None = None,
    ) -> dict:
        try:
            async with stdio_client(self.server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    result = await asyncio.wait_for(
                        session.call_tool(
                            "retrieve_chunks",
                            {
                                "project_id": project_id,
                                "query": query,
                                "top_k": top_k,
                                "user_id": user_id,
                            },
                        ),
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
            return error_response("TIMEOUT", "rag_mcp_server", "RAG MCP server timed out.")
        except Exception as exc:
            return error_response(
                "MCP_TOOL_FAILURE",
                "rag_mcp_server",
                "RAG MCP server failed while executing a tool.",
                details=str(exc),
            )


mcp_rag_client = MCPRagClient()
