import os
import requests
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

load_dotenv()

SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")

mcp = FastMCP("notification-server")


@mcp.tool()
def draft_slack_update(
    project_name: str,
    tasks_created: int,
    approved_tasks: int,
    github_issues_created: int,
) -> dict:
    message = f"""
🚀 Project Update: {project_name}

Tasks generated: {tasks_created}
Tasks approved: {approved_tasks}
GitHub issues created: {github_issues_created}

Status: Project planning workflow is progressing successfully.
"""

    return {
        "status": "drafted",
        "message": message.strip(),
    }


@mcp.tool()
def send_slack_message(channel_id: str, message: str) -> dict:
    if not SLACK_BOT_TOKEN:
        raise RuntimeError("SLACK_BOT_TOKEN is missing.")

    url = "https://slack.com/api/chat.postMessage"

    headers = {
        "Authorization": f"Bearer {SLACK_BOT_TOKEN}",
        "Content-Type": "application/json; charset=utf-8",
    }

    payload = {
        "channel": channel_id,
        "text": message,
    }

    response = requests.post(url, headers=headers, json=payload, timeout=30)
    response.raise_for_status()

    data = response.json()

    if not data.get("ok"):
        raise RuntimeError(f"Slack API error: {data}")

    return {
        "ok": True,
        "channel": data.get("channel"),
        "ts": data.get("ts"),
        "message": message,
    }


if __name__ == "__main__":
    mcp.run()
