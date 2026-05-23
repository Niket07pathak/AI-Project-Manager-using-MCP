import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


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
    ) -> dict:
        async with stdio_client(self.server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()

                result = await session.call_tool(
                    "search_project_docs",
                    {
                        "project_id": project_id,
                        "query": query,
                        "top_k": top_k,
                    },
                )

                content = result.content[0]

                if hasattr(content, "text"):
                    import json

                    return json.loads(content.text)

                return result

    def search_project_docs(
        self,
        project_id: int,
        query: str,
        top_k: int = 5,
    ) -> dict:
        return asyncio.run(
            self.search_project_docs_async(
                project_id=project_id,
                query=query,
                top_k=top_k,
            )
        )


mcp_rag_client = MCPRagClient()
