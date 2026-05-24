import os

from backend.app.services.mcp_task_client import mcp_task_client

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

print(result)
