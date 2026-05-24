import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app import crud, schemas
from backend.app.auth import CurrentUser, get_current_user
from backend.app.database import get_db
from backend.app.services.errors import error_message, is_error_response
from backend.app.services.mcp_notification_client import mcp_notification_client
from backend.app.services.mcp_task_client import mcp_task_client

router = APIRouter(tags=["notifications"])


@router.post("/projects/{project_id}/notifications/slack/draft")
def draft_project_slack_update(
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

    tasks = crud.get_tasks_by_project_and_user(
        db=db,
        project_id=project_id,
        user_id=current_user.user_id,
    )
    approved_tasks = [task for task in tasks if task.approved is True]

    github_issues = crud.get_github_issues_by_project_and_user(
        db=db,
        project_id=project_id,
        user_id=current_user.user_id,
    )

    draft = mcp_notification_client.draft_slack_update(
        project_name=project.name,
        tasks_created=len(tasks),
        approved_tasks=len(approved_tasks),
        github_issues_created=len(github_issues),
    )
    if is_error_response(draft):
        raise HTTPException(
            status_code=502,
            detail=error_message(draft, "Slack update draft failed."),
        )

    mcp_task_client.create_audit_log(
        project_id=project_id,
        user_id=current_user.user_id,
        action="slack_update_drafted",
        tool_name="notification_mcp_server",
        input_data=json.dumps(
            {
                "project_name": project.name,
                "tasks_created": len(tasks),
                "approved_tasks": len(approved_tasks),
                "github_issues_created": len(github_issues),
            }
        ),
        output_data=json.dumps(draft),
        status="success",
    )

    return {
        "project_id": project_id,
        "slack_channel_id": project.slack_channel_id,
        "slack_channel_name": project.slack_channel_name,
        "draft": draft,
    }


@router.post("/projects/{project_id}/notifications/slack/send")
def send_project_slack_update(
    project_id: int,
    payload: schemas.SlackSendRequest,
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

    if not project.slack_channel_id:
        raise HTTPException(
            status_code=400,
            detail="Slack channel is not configured for this project.",
        )

    workflow_run = crud.create_workflow_run(
        db=db,
        workflow_run=schemas.WorkflowRunCreate(
            project_id=project_id,
            user_id=current_user.user_id,
            workflow_type="slack_notification",
            status="running",
            input_data=json.dumps(
                {
                    "project_id": project_id,
                    "channel_id": project.slack_channel_id,
                    "channel_name": project.slack_channel_name,
                    "message": payload.message,
                }
            ),
        ),
    )

    try:
        result = mcp_notification_client.send_slack_message(
            channel_id=project.slack_channel_id,
            message=payload.message,
        )
        if is_error_response(result):
            raise HTTPException(
                status_code=502,
                detail=error_message(result, "Slack message failed."),
            )

        mcp_task_client.create_audit_log(
            project_id=project_id,
            user_id=current_user.user_id,
            action="slack_message_sent",
            tool_name="notification_mcp_server",
            input_data=json.dumps(
                {
                    "channel_id": project.slack_channel_id,
                    "channel_name": project.slack_channel_name,
                    "message": payload.message,
                }
            ),
            output_data=json.dumps(result),
            status="success",
        )

        response = {
            "project_id": project_id,
            "channel_id": project.slack_channel_id,
            "channel_name": project.slack_channel_name,
            "result": result,
        }

        crud.update_workflow_run(
            db=db,
            workflow_run_id=workflow_run.id,
            workflow_run=schemas.WorkflowRunUpdate(
                status="success",
                output_data=json.dumps(response),
                error_message=None,
            ),
        )

        return response

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
        raise HTTPException(status_code=502, detail="Slack notification failed.") from e
