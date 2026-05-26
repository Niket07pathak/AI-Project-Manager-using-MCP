import os
import sys
from pathlib import Path
import logging
import requests
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from backend.app.services.errors import error_response

load_dotenv()
logger = logging.getLogger(__name__)

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
        logger.warning("Slack bot token is missing")
        return error_response(
            "CONFIGURATION_ERROR",
            "slack",
            "Slack bot token is not configured.",
        )

    url = "https://slack.com/api/chat.postMessage"

    headers = {
        "Authorization": f"Bearer {SLACK_BOT_TOKEN}",
        "Content-Type": "application/json; charset=utf-8",
    }

    payload = {
        "channel": channel_id,
        "text": message,
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()
    except requests.Timeout:
        logger.warning("Slack API timed out for channel %s", channel_id)
        return error_response("TIMEOUT", "slack", "Slack API timed out.")
    except requests.RequestException as exc:
        logger.warning("Slack API request failed: %s", exc)
        return error_response(
            "SERVICE_UNAVAILABLE",
            "slack",
            "Slack is unavailable. Please try again later.",
        )
    except ValueError as exc:
        logger.warning("Slack returned invalid JSON: %s", exc)
        return error_response("INVALID_RESPONSE", "slack", "Slack returned an invalid response.")

    if not data.get("ok"):
        error_code = data.get("error")
        logger.warning("Slack API returned error for channel %s: %s", channel_id, error_code)
        message = "Slack rejected the message."
        if error_code in {"channel_not_found", "invalid_channel"}:
            message = "Slack channel was not found or is invalid."
        elif error_code in {"not_in_channel", "no_permission", "missing_scope"}:
            message = "Slack bot does not have permission to post in this channel."
        elif error_code == "ratelimited":
            message = "Slack rate limit reached. Please try again later."
        return error_response("BAD_RESPONSE", "slack", message)

    return {
        "ok": True,
        "channel": data.get("channel"),
        "ts": data.get("ts"),
        "message": message,
    }


if __name__ == "__main__":
    mcp.run()
