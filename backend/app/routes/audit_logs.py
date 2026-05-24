from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app import crud, schemas
from backend.app.auth import AuthContext, CurrentUser, get_current_user, get_current_user_or_internal
from backend.app.database import get_db

router = APIRouter(tags=["audit_logs"])


@router.post("/audit-logs")
def create_audit_log(
    audit_log: schemas.AuditLogCreate,
    db: Session = Depends(get_db),
    auth_context: AuthContext = Depends(get_current_user_or_internal),
):
    user_id = audit_log.user_id if auth_context.is_internal else auth_context.user_id
    if not user_id:
        raise HTTPException(status_code=401, detail="User context is required")

    if audit_log.project_id is not None:
        project = crud.get_project_by_id_and_user(
            db=db,
            project_id=audit_log.project_id,
            user_id=user_id,
        )
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

    audit_log.user_id = user_id
    return crud.create_audit_log(db=db, audit_log=audit_log)


@router.get(
    "/projects/{project_id}/audit-logs", response_model=list[schemas.AuditLogResponse]
)
def list_project_audit_logs(
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

    return crud.get_audit_logs_by_project_and_user(
        db=db,
        project_id=project_id,
        user_id=current_user.user_id,
    )
