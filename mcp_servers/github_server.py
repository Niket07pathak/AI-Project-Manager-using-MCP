import os
import requests
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

load_dotenv()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPO_OWNER = os.getenv("GITHUB_REPO_OWNER")
GITHUB_REPO_NAME = os.getenv("GITHUB_REPO_NAME")

if not GITHUB_TOKEN:
    raise RuntimeError("GitHub configuration is missing in environment variables.")

mcp = FastMCP("github-server")


def github_headers():
    return {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


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

    response = requests.post(
        url,
        headers=github_headers(),
        json=payload,
        timeout=30,
    )
    response.raise_for_status()

    data = response.json()

    return {
        "issue_number": data["number"],
        "issue_url": data["html_url"],
        "title": data["title"],
        "state": data["state"],
    }


@mcp.tool()
def list_repo_issues(state: str = "open") -> dict:
    """
    List GitHub issues from the configured repository.
    """
    url = f"https://api.github.com/repos/{GITHUB_REPO_OWNER}/{GITHUB_REPO_NAME}/issues"

    response = requests.get(
        url,
        headers=github_headers(),
        params={"state": state},
        timeout=30,
    )
    response.raise_for_status()

    issues = response.json()

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

    response = requests.post(
        url,
        headers=github_headers(),
        json=payload,
        timeout=30,
    )
    response.raise_for_status()

    data = response.json()

    return {
        "comment_url": data["html_url"],
        "issue_number": issue_number,
    }


if __name__ == "__main__":
    mcp.run()
