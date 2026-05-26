import os
import logging

from backend.app.services.mcp_task_client import mcp_task_client

logger = logging.getLogger(__name__)

result = mcp_task_client.create_audit_log(
    project_id=6,
    user_id=os.getenv("CLERK_TEST_USER_ID", "dev-user"),
    action="mcp_audit_test",
    tool_name="debug_mcp_task_client",
    input_data="test input",
    output_data="test output",
    status="success",
    auth_token=os.getenv("CLERK_TEST_JWT"),
)

logger.info("MCP audit test completed with success=%s", result.get("success", True))
