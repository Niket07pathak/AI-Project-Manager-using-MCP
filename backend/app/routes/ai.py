from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app import crud, schemas
from backend.app.agents.project_analyzer import analyze_project_with_langgraph
from backend.app.auth import CurrentUser, get_current_user
from backend.app.config import is_development
from backend.app.database import get_db
from backend.app.services.embedding_provider import embedding_provider
from backend.app.services.errors import public_error_detail
from backend.app.services.llm_provider import llm_provider
import json

router = APIRouter(tags=["ai"])


@router.get("/health")
def health_check():
    return {"status": "healthy"}


def require_development_mode():
    if not is_development():
        raise HTTPException(status_code=404, detail="Not found")


@router.post("/ai/test-generate", dependencies=[Depends(require_development_mode)])
def test_generate():
    response = llm_provider.generate("Reply with only: Hello from Ollama.")
    return {
        "provider": llm_provider.provider,
        "model": llm_provider.model,
        "response": response,
    }


@router.get("/ai/embedding-health", dependencies=[Depends(require_development_mode)])
def embedding_health():
    return embedding_provider.health()


@router.post("/ai/test-embed", dependencies=[Depends(require_development_mode)])
def test_embed():
    text = "This is a test document for embedding."
    embedding = embedding_provider.embed(text)
    return {
        "provider": embedding_provider.provider,
        "model": embedding_provider.model,
        "dimension": len(embedding),
        "sample": embedding[:5],
    }


@router.post(
    "/projects/{project_id}/analyze", response_model=schemas.ProjectAnalyzeResponse
)
def analyze_project_endpoint(
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

    workflow_run = crud.create_workflow_run(
        db=db,
        workflow_run=schemas.WorkflowRunCreate(
            project_id=project_id,
            user_id=current_user.user_id,
            workflow_type="analyze_project",
            status="running",
            input_data=json.dumps({"project_id": project_id}),
        ),
    )

    try:
        result = analyze_project_with_langgraph(
            project_id=project_id,
            user_id=current_user.user_id,
            db=db,
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

        return {
            "project_id": result["project_id"],
            "chunks_used": result["chunks_used"],
            "tasks_created": result["tasks_created"],
        }

    except Exception as e:
        crud.update_workflow_run(
            db=db,
            workflow_run_id=workflow_run.id,
            workflow_run=schemas.WorkflowRunUpdate(
                status="failed",
                output_data=None,
                error_message=public_error_detail(
                    e,
                    "Project analysis failed. Please check dependent services and try again.",
                ),
            ),
        )
        raise HTTPException(
            status_code=503,
            detail="Project analysis failed. Please check dependent services and try again.",
        ) from e
