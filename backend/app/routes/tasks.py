from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.app import crud, schemas
from backend.app.auth import AuthContext, CurrentUser, get_current_user, get_current_user_or_internal
from backend.app.database import get_db
from backend.app.services.mcp_task_client import mcp_task_client

router = APIRouter(tags=["tasks"])


@router.post("/tasks", response_model=schemas.TaskResponse)
def create_task(
    task: schemas.TaskCreate,
    db: Session = Depends(get_db),
    auth_context: AuthContext = Depends(get_current_user_or_internal),
):
    user_id = task.user_id if auth_context.is_internal else auth_context.user_id
    if not user_id:
        raise HTTPException(status_code=401, detail="User context is required")

    project = crud.get_project_by_id_and_user(
        db=db,
        project_id=task.project_id,
        user_id=user_id,
    )
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    task.user_id = user_id
    return crud.create_task(db=db, task=task)


@router.get("/project/{project_id}/tasks", response_model=list[schemas.TaskResponse])
def list_project_tasks(
    project_id: int,
    user_id: str | None = Query(default=None),
    db: Session = Depends(get_db),
    auth_context: AuthContext = Depends(get_current_user_or_internal),
):
    effective_user_id = user_id if auth_context.is_internal else auth_context.user_id
    if not effective_user_id:
        raise HTTPException(status_code=401, detail="User context is required")

    project = crud.get_project_by_id_and_user(
        db=db,
        project_id=project_id,
        user_id=effective_user_id,
    )
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    return crud.get_tasks_by_project_and_user(
        db=db,
        project_id=project_id,
        user_id=effective_user_id,
    )


@router.patch("/tasks/{task_id}/edit", response_model=schemas.TaskResponse)
def edit_task(
    task_id: int,
    payload: schemas.TaskEditUpdate,
    user_id: str | None = Query(default=None),
    db: Session = Depends(get_db),
    auth_context: AuthContext = Depends(get_current_user_or_internal),
):
    effective_user_id = user_id if auth_context.is_internal else auth_context.user_id
    if not effective_user_id:
        raise HTTPException(status_code=401, detail="User context is required")

    existing_task = crud.get_task_by_id(db=db, task_id=task_id)
    if not existing_task or existing_task.user_id != effective_user_id:
        raise HTTPException(status_code=404, detail="Task not found")

    task = crud.edit_task(db=db, task_id=task_id, payload=payload)

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    audit_data = schemas.AuditLogCreate(
        project_id=task.project_id,
        action="task_edited",
        tool_name="task_approval_system",
        user_id=effective_user_id,
        input_data=payload.model_dump_json(),
        output_data=f"task_id={task.id}",
        status="success",
    )
    mcp_task_client.create_audit_log(
        project_id=audit_data.project_id,
        user_id=effective_user_id,
        action=audit_data.action,
        tool_name=audit_data.tool_name,
        input_data=audit_data.input_data,
        output_data=audit_data.output_data,
        status=audit_data.status,
    )

    return task


@router.patch("/tasks/{task_id}/approve", response_model=schemas.TaskResponse)
def approve_task(
    task_id: int,
    user_id: str | None = Query(default=None),
    db: Session = Depends(get_db),
    auth_context: AuthContext = Depends(get_current_user_or_internal),
):
    effective_user_id = user_id if auth_context.is_internal else auth_context.user_id
    if not effective_user_id:
        raise HTTPException(status_code=401, detail="User context is required")

    existing_task = crud.get_task_by_id(db=db, task_id=task_id)
    if not existing_task or existing_task.user_id != effective_user_id:
        raise HTTPException(status_code=404, detail="Task not found")

    task = crud.approve_task(db=db, task_id=task_id)

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    audit_data = schemas.AuditLogCreate(
        project_id=task.project_id,
        action="task_approved",
        tool_name="task_approval_system",
        user_id=effective_user_id,
        input_data=f"task_id={task.id}",
        output_data=f"status={task.status}, approved={task.approved}",
        status="success",
    )
    mcp_task_client.create_audit_log(
        project_id=audit_data.project_id,
        user_id=effective_user_id,
        action=audit_data.action,
        tool_name=audit_data.tool_name,
        input_data=audit_data.input_data,
        output_data=audit_data.output_data,
        status=audit_data.status,
    )

    return task


@router.patch("/tasks/{task_id}/reject", response_model=schemas.TaskResponse)
def reject_task(
    task_id: int,
    user_id: str | None = Query(default=None),
    db: Session = Depends(get_db),
    auth_context: AuthContext = Depends(get_current_user_or_internal),
):
    effective_user_id = user_id if auth_context.is_internal else auth_context.user_id
    if not effective_user_id:
        raise HTTPException(status_code=401, detail="User context is required")

    existing_task = crud.get_task_by_id(db=db, task_id=task_id)
    if not existing_task or existing_task.user_id != effective_user_id:
        raise HTTPException(status_code=404, detail="Task not found")

    task = crud.reject_task(db=db, task_id=task_id)

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    audit_data = schemas.AuditLogCreate(
        project_id=task.project_id,
        action="task_rejected",
        tool_name="task_approval_system",
        user_id=effective_user_id,
        input_data=f"task_id={task.id}",
        output_data=f"status={task.status}, approved={task.approved}",
        status="success",
    )
    mcp_task_client.create_audit_log(
        project_id=audit_data.project_id,
        user_id=effective_user_id,
        action=audit_data.action,
        tool_name=audit_data.tool_name,
        input_data=audit_data.input_data,
        output_data=audit_data.output_data,
        status=audit_data.status,
    )

    return task


@router.delete("/tasks/{task_id}")
def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    existing_task = crud.get_task_by_id(db=db, task_id=task_id)
    if not existing_task or existing_task.user_id != current_user.user_id:
        raise HTTPException(status_code=404, detail="Task not found")

    task = crud.delete_task(db=db, task_id=task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"success": True, "message": f"Task with id {task_id} has been deleted."}
