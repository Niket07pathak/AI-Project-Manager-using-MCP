from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app import crud, schemas
from backend.app.auth import CurrentUser, get_current_user
from backend.app.database import get_db

router = APIRouter(tags=["Workflow Runs"])


@router.get(
    "/projects/{project_id}/workflow-runs",
    response_model=list[schemas.WorkflowRunResponse],
)
def list_project_workflow_runs(
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

    return crud.get_workflow_runs_by_project_and_user(
        db=db,
        project_id=project_id,
        user_id=current_user.user_id,
    )
