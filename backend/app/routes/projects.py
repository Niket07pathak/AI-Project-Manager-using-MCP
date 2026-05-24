from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app import crud, schemas
from backend.app.auth import CurrentUser, get_current_user
from backend.app.database import get_db

router = APIRouter(tags=["projects"])


@router.post("/projects", response_model=schemas.ProjectResponse)
def create_project(
    project: schemas.ProjectCreate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    return crud.create_project_for_user(
        db=db,
        project=project,
        user_id=current_user.user_id,
    )


@router.get("/projects", response_model=list[schemas.ProjectResponse])
def list_projects(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    return crud.get_projects_by_user(db=db, user_id=current_user.user_id)


@router.get("/projects/{project_id}", response_model=schemas.ProjectResponse)
def get_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    db_project = crud.get_project_by_id_and_user(
        db=db,
        project_id=project_id,
        user_id=current_user.user_id,
    )
    if not db_project:
        raise HTTPException(status_code=404, detail="Project not found")
    return db_project


@router.patch("/projects/{project_id}/status", response_model=schemas.ProjectResponse)
def update_project_status(
    project_id: int,
    payload: schemas.StatusUpdate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    db_project = crud.update_project_status_for_user(
        db=db,
        project_id=project_id,
        user_id=current_user.user_id,
        status=payload.status,
    )
    if not db_project:
        raise HTTPException(status_code=404, detail="Project not found")
    return db_project


@router.delete("/projects/{project_id}")
def delete_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    project = crud.delete_project_for_user(
        db=db,
        project_id=project_id,
        user_id=current_user.user_id,
    )
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return {
        "success": True,
        "message": f"Project with id {project_id} has been deleted.",
    }
