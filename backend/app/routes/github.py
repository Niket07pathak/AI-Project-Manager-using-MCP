import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app import crud, schemas
from backend.app.auth import CurrentUser, get_current_user
from backend.app.database import get_db
from backend.app.services.errors import error_message, is_error_response
from backend.app.services.mcp_github_client import mcp_github_client
from backend.app.services.mcp_task_client import mcp_task_client

router = APIRouter(tags=["github"])


@router.post("/projects/{project_id}/github/issues/create")
def create_github_issues_for_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    project = crud.get_project_by_id_and_user(
        db=db,
        project_id=project_id,
        user_id=current_user.user_id,
    )

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if not project.github_repo_owner or not project.github_repo_name:
        raise HTTPException(
            status_code=400,
            detail="GitHub repo is not configured for this project.",
        )

    workflow_run = crud.create_workflow_run(
        db=db,
        workflow_run=schemas.WorkflowRunCreate(
            project_id=project_id,
            user_id=current_user.user_id,
            workflow_type="github_issue_creation",
            status="running",
            input_data=json.dumps(
                {
                    "project_id": project_id,
                    "repo_owner": project.github_repo_owner,
                    "repo_name": project.github_repo_name,
                }
            ),
        ),
    )

    try:
        approved_tasks = crud.get_approved_tasks_by_project_and_user(
            db=db,
            project_id=project_id,
            user_id=current_user.user_id,
        )

        if not approved_tasks:
            raise HTTPException(
                status_code=400,
                detail="No approved tasks found for this project.",
            )

        created_issues = []
        skipped_tasks = []

        for task in approved_tasks:
            existing_issue = crud.get_github_issue_by_task_id_and_user(
                db=db,
                task_id=task.id,
                user_id=current_user.user_id,
            )

            if existing_issue:
                skipped_tasks.append(
                    {
                        "task_id": task.id,
                        "reason": "GitHub issue already exists",
                        "issue_url": existing_issue.issue_url,
                    }
                )
                continue

            issue_body = f"""
## Task Description

{task.description or "No description provided."}

## Metadata

- Project ID: {project_id}
- Task ID: {task.id}
- Priority: {task.priority}
- Status: {task.status}

Created by AI Project Manager after human approval.
"""

            github_result = mcp_github_client.create_github_issue(
                repo_owner=project.github_repo_owner,
                repo_name=project.github_repo_name,
                title=task.title,
                body=issue_body,
                labels=["ai-generated", task.priority],
            )
            if is_error_response(github_result):
                raise HTTPException(
                    status_code=502,
                    detail=error_message(github_result, "GitHub issue creation failed."),
                )

            issue_record = schemas.GitHubIssueCreate(
                user_id=current_user.user_id,
                project_id=project_id,
                task_id=task.id,
                issue_number=github_result["issue_number"],
                issue_url=github_result["issue_url"],
                title=github_result["title"],
            )

            saved_issue = crud.create_github_issue_record(
                db=db,
                issue=issue_record,
            )

            created_issues.append(
                {
                    "task_id": task.id,
                    "issue_number": saved_issue.issue_number,
                    "issue_url": saved_issue.issue_url,
                    "title": saved_issue.title,
                }
            )

        result = {
            "project_id": project_id,
            "issues_created": len(created_issues),
            "issues": created_issues,
            "skipped_tasks": skipped_tasks,
        }

        mcp_task_client.create_audit_log(
            project_id=project_id,
            user_id=current_user.user_id,
            action="github_issues_created",
            tool_name="github_mcp_server",
            input_data=json.dumps(
                {
                    "approved_task_count": len(approved_tasks),
                    "task_ids": [task.id for task in approved_tasks],
                }
            ),
            output_data=json.dumps(result),
            status="success",
        )

        crud.update_workflow_run(
            db=db,
            workflow_run_id=workflow_run.id,
            workflow_run=schemas.WorkflowRunUpdate(
                status="success",
                output_data=json.dumps(result),
                error_message=None,
            ),
        )

        return result

    except Exception as e:
        crud.update_workflow_run(
            db=db,
            workflow_run_id=workflow_run.id,
            workflow_run=schemas.WorkflowRunUpdate(
                status="failed",
                output_data=None,
                error_message=str(e),
            ),
        )
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(status_code=502, detail="GitHub issue creation failed.") from e

@router.get(
    "/projects/{project_id}/github/issues",
    response_model=list[schemas.GitHubIssueResponse],
)
def list_project_github_issues(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    project = crud.get_project_by_id_and_user(
        db=db,
        project_id=project_id,
        user_id=current_user.user_id,
    )

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    return crud.get_github_issues_by_project_and_user(
        db=db,
        project_id=project_id,
        user_id=current_user.user_id,
    )
