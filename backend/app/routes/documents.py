import logging
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy.orm import Session

from backend.app import crud, schemas
from backend.app.auth import AuthContext, CurrentUser, get_current_user, get_current_user_or_internal
from backend.app.database import get_db
from backend.app.services.errors import ServiceError
from backend.app.services.document_processor import document_processor
from backend.app.services.embedding_provider import embedding_provider
from backend.app.services.qdrant_provider import qdrant_provider
from backend.app.services.storage_provider import storage_provider

router = APIRouter(tags=["documents"])
logger = logging.getLogger(__name__)


@router.post("/documents", response_model=schemas.DocumentResponse)
def create_document(
    document: schemas.DocumentCreate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    project = crud.get_project_by_id_and_user(
        db=db,
        project_id=document.project_id,
        user_id=current_user.user_id,
    )
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    document.user_id = current_user.user_id
    return crud.create_document(db=db, document=document)


@router.get(
    "/projects/{project_id}/documents", response_model=list[schemas.DocumentResponse]
)
def list_project_dosuments(
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

    return crud.get_documents_by_project_id_and_user(
        db=db,
        project_id=project_id,
        user_id=current_user.user_id,
    )


@router.get("/documents/{document_id}", response_model=schemas.DocumentResponse)
def get_document(
    document_id: int,
    user_id: str | None = Query(default=None),
    db: Session = Depends(get_db),
    auth_context: AuthContext = Depends(get_current_user_or_internal),
):
    effective_user_id = user_id if auth_context.is_internal else auth_context.user_id
    if not effective_user_id:
        raise HTTPException(status_code=401, detail="User context is required")

    document = crud.get_document_by_id(db=db, document_id=document_id)
    if not document or document.user_id != effective_user_id:
        raise HTTPException(status_code=404, detail="Document not found")
    return document


@router.patch("/documents/{document_id}/status", response_model=schemas.DocumentResponse)
def update_document_status(
    document_id: int,
    payload: schemas.StatusUpdate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    existing_document = crud.get_document_by_id(db=db, document_id=document_id)
    if not existing_document or existing_document.user_id != current_user.user_id:
        raise HTTPException(status_code=404, detail="Document not found")

    document = crud.update_document_status(
        db=db, document_id=document_id, status=payload.status
    )
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    return document


@router.delete("/documents/{document_id}")
def delete_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    existing_document = crud.get_document_by_id(db=db, document_id=document_id)
    if not existing_document or existing_document.user_id != current_user.user_id:
        raise HTTPException(status_code=404, detail="Document not found")

    document = crud.delete_document(db=db, document_id=document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    return {
        "success": True,
        "message": f"Document with id {document_id} has been deleted.",
    }


@router.post(
    "/projects/{project_id}/documents/upload", response_model=schemas.DocumentResponse
)
async def upload_project_document(
    project_id: int,
    file: UploadFile = File(...),
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

    file_bytes = await file.read()

    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is missing")

    storage_path = storage_provider.upload_file(
        project_id=project_id,
        filename=file.filename,
        file_bytes=file_bytes,
        content_type=file.content_type,
    )

    document_data = schemas.DocumentCreate(
        user_id=current_user.user_id,
        project_id=project_id,
        filename=file.filename,
        filetype=file.content_type,
        storage_path=storage_path,
    )

    document = crud.create_document(db=db, document=document_data)

    return document


@router.post("/documents/{document_id}/process")
def process_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    document = crud.get_document_by_id(db=db, document_id=document_id)

    if not document or document.user_id != current_user.user_id:
        raise HTTPException(status_code=404, detail="Document not found")

    if not document.storage_path:
        raise HTTPException(status_code=400, detail="Document has no storage path")

    file_bytes = storage_provider.download_file(document.storage_path)

    text = document_processor.extract_text(
        filename=document.filename,
        file_bytes=file_bytes,
    )

    if not text.strip():
        raise HTTPException(status_code=400, detail="No text could be extracted")

    chunks = document_processor.chunk_text(text)

    saved_chunks = []

    for index, chunk in enumerate(chunks):
        try:
            embedding = embedding_provider.embed(chunk)
        except ServiceError as exc:
            logger.warning("Document processing embedding failed for document %s: %s", document_id, exc.message)
            raise HTTPException(status_code=503, detail=exc.message) from exc

        chunk_data = schemas.DocumentChunkCreate(
            user_id=current_user.user_id,
            document_id=document.id,
            project_id=document.project_id,
            chunk_index=index,
            content=chunk,
            qdrant_point_id=None,
            token_count=len(chunk.split()),
        )

        saved_chunk = crud.create_document_chunk(
            db=db,
            document_chunk=chunk_data,
        )

        try:
            qdrant_point_id = qdrant_provider.upsert_chunk(
                embedding=embedding,
                project_id=document.project_id,
                document_id=document.id,
                chunk_id=saved_chunk.id,
                chunk_index=index,
                content=chunk,
            )
        except ServiceError as exc:
            logger.warning("Qdrant upsert failed for document %s: %s", document_id, exc.message)
            raise HTTPException(status_code=503, detail=exc.message) from exc

        saved_chunk.qdrant_point_id = qdrant_point_id
        db.commit()
        db.refresh(saved_chunk)

        saved_chunks.append(saved_chunk)
    crud.update_document_status(
        db=db,
        document_id=document.id,
        status="processed",
    )

    return {
        "document_id": document.id,
        "project_id": document.project_id,
        "chunks_created": len(saved_chunks),
        "status": "processed",
    }


@router.get(
    "/projects/{project_id}/chunks", response_model=list[schemas.DocumentChunkResponse]
)
def list_project_chunks(
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

    return crud.get_chunks_by_project_and_user(
        db=db,
        project_id=project_id,
        user_id=current_user.user_id,
    )


@router.get(
    "/documents/{document_id}/chunks",
    response_model=list[schemas.DocumentChunkResponse],
)
def list_document_chunks(
    document_id: int,
    user_id: str | None = Query(default=None),
    db: Session = Depends(get_db),
    auth_context: AuthContext = Depends(get_current_user_or_internal),
):
    effective_user_id = user_id if auth_context.is_internal else auth_context.user_id
    if not effective_user_id:
        raise HTTPException(status_code=401, detail="User context is required")

    document = crud.get_document_by_id(db=db, document_id=document_id)
    if not document or document.user_id != effective_user_id:
        raise HTTPException(status_code=404, detail="Document not found")

    return crud.get_chunks_by_document_and_user(
        db=db,
        document_id=document_id,
        user_id=effective_user_id,
    )


@router.post("/projects/{project_id}/search")
def search_project_documents(
    project_id: int,
    payload: schemas.ProjectSearchRequest,
    db: Session = Depends(get_db),
    auth_context: AuthContext = Depends(get_current_user_or_internal),
):
    user_id = payload.user_id if auth_context.is_internal else auth_context.user_id
    if not user_id:
        raise HTTPException(status_code=401, detail="User context is required")

    project = crud.get_project_by_id_and_user(
        db=db,
        project_id=project_id,
        user_id=user_id,
    )

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    try:
        query_embedding = embedding_provider.embed(payload.query)
    except ServiceError as exc:
        logger.warning("Search embedding failed for project %s: %s", project_id, exc.message)
        raise HTTPException(status_code=503, detail=exc.message) from exc

    try:
        results = qdrant_provider.search_chunks(
            query_embedding=query_embedding,
            project_id=project_id,
            top_k=payload.top_k,
        )
    except ServiceError as exc:
        logger.warning("Qdrant search failed for project %s: %s", project_id, exc.message)
        raise HTTPException(status_code=503, detail=exc.message) from exc

    return {
        "project_id": project_id,
        "query": payload.query,
        "results": [
            {
                "score": result.score,
                "chunk_id": result.payload.get("chunk_id"),
                "document_id": result.payload.get("document_id"),
                "chunk_index": result.payload.get("chunk_index"),
                "content": result.payload.get("content"),
            }
            for result in results
        ],
    }
