import os
import logging
import requests
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from backend.app.services.errors import error_response

load_dotenv()
logger = logging.getLogger(__name__)

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPO_OWNER = os.getenv("GITHUB_REPO_OWNER")
GITHUB_REPO_NAME = os.getenv("GITHUB_REPO_NAME")

mcp = FastMCP("github-server")


def github_headers():
    if not GITHUB_TOKEN:
        raise RuntimeError("GITHUB_TOKEN is missing.")
    return {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def response_json(response: requests.Response) -> dict:
    try:
        return response.json()
    except ValueError:
        logger.warning("GitHub returned invalid JSON")
        return error_response(
            "INVALID_RESPONSE",
            "github",
            "GitHub returned an invalid response.",
        )


@mcp.tool()
def create_github_issue(
    repo_owner: str,
    repo_name: str,
    title: str,
    body: str,
    labels: list[str] | None = None,
) -> dict:
    url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/issues"

    payload = {
        "title": title,
        "body": body,
        "labels": labels or [],
    }

    try:
        response = requests.post(
            url,
            headers=github_headers(),
            json=payload,
            timeout=30,
        )
        response.raise_for_status()
    except RuntimeError as exc:
        logger.warning("GitHub configuration error: %s", exc)
        return error_response(
            "CONFIGURATION_ERROR",
            "github",
            "GitHub token is not configured.",
        )
    except requests.HTTPError as exc:
        status_code = exc.response.status_code if exc.response is not None else None
        logger.warning("GitHub create issue failed (%s): %s", status_code, exc)
        message = "GitHub API rejected issue creation."
        if status_code == 404:
            message = "GitHub repository was not found."
        elif status_code in (401, 403):
            message = "GitHub token does not have permission for this repository."
        elif status_code == 429:
            message = "GitHub rate limit reached. Please try again later."
        return error_response("BAD_RESPONSE", "github", message)
    except requests.RequestException as exc:
        logger.warning("GitHub create issue request failed: %s", exc)
        return error_response(
            "SERVICE_UNAVAILABLE",
            "github",
            "GitHub is unavailable. Please try again later.",
        )

    data = response_json(response)
    if data.get("success") is False:
        return data

    return {
        "issue_number": data.get("number"),
        "issue_url": data.get("html_url"),
        "title": data.get("title"),
        "state": data.get("state"),
    }


@mcp.tool()
def list_repo_issues(state: str = "open") -> dict:
    """
    List GitHub issues from the configured repository.
    """
    url = f"https://api.github.com/repos/{GITHUB_REPO_OWNER}/{GITHUB_REPO_NAME}/issues"

    try:
        response = requests.get(
            url,
            headers=github_headers(),
            params={"state": state},
            timeout=30,
        )
        response.raise_for_status()
    except RuntimeError as exc:
        logger.warning("GitHub configuration error: %s", exc)
        return error_response("CONFIGURATION_ERROR", "github", "GitHub token is not configured.")
    except requests.RequestException as exc:
        logger.warning("GitHub list issues failed: %s", exc)
        return error_response("BAD_RESPONSE", "github", "Could not list GitHub issues.")

    issues = response_json(response)
    if isinstance(issues, dict) and issues.get("success") is False:
        return issues

    return {
        "repo": f"{GITHUB_REPO_OWNER}/{GITHUB_REPO_NAME}",
        "issues": [
            {
                "issue_number": issue["number"],
                "title": issue["title"],
                "state": issue["state"],
                "issue_url": issue["html_url"],
            }
            for issue in issues
        ],
    }


@mcp.tool()
def comment_on_issue(issue_number: int, comment: str) -> dict:
    """
    Add a comment to a GitHub issue.
    """
    url = f"https://api.github.com/repos/{GITHUB_REPO_OWNER}/{GITHUB_REPO_NAME}/issues/{issue_number}/comments"

    payload = {
        "body": comment,
    }

    try:
        response = requests.post(
            url,
            headers=github_headers(),
            json=payload,
            timeout=30,
        )
        response.raise_for_status()
    except RuntimeError as exc:
        logger.warning("GitHub configuration error: %s", exc)
        return error_response("CONFIGURATION_ERROR", "github", "GitHub token is not configured.")
    except requests.RequestException as exc:
        logger.warning("GitHub comment failed: %s", exc)
        return error_response("BAD_RESPONSE", "github", "Could not comment on GitHub issue.")

    data = response_json(response)
    if data.get("success") is False:
        return data

    return {
        "comment_url": data.get("html_url"),
        "issue_number": issue_number,
    }


if __name__ == "__main__":
    mcp.run()
