from fastapi import FastAPI, Depends, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from backend.app import models, schemas, crud
from backend.app.database import engine, get_db, Base

from backend.app.services.llm_provider import llm_provider

from backend.app.services.embedding_provider import embedding_provider
from backend.app.services.storage_provider import storage_provider
from backend.app.services.document_processor import document_processor
from backend.app.services.qdrant_provider import qdrant_provider

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="AI Project Manager API",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {
        "message": "AI Project Manager API is running. Use /docs for API documentation."
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}


@app.post("/projects", response_model=schemas.ProjectResponse)
def create_project(project: schemas.ProjectCreate, db: Session = Depends(get_db)):
    return crud.create_project(db=db, project=project)


@app.get("/projects", response_model=list[schemas.ProjectResponse])
def list_projects(db: Session = Depends(get_db)):
    return crud.get_project(db=db)


@app.get("/projects/{project_id}", response_model=schemas.ProjectResponse)
def get_project(project_id: int, db: Session = Depends(get_db)):
    db_project = crud.get_project_by_id(db=db, project_id=project_id)
    if not db_project:
        raise HTTPException(status_code=404, detail="Project not found")
    return db_project


@app.patch("/projects/{project_id}/status", response_model=schemas.ProjectResponse)
def update_project_status(
    project_id: int, payload: schemas.StatusUpdate, db: Session = Depends(get_db)
):
    db_project = crud.update_project_status(
        db=db, project_id=project_id, status=payload.status
    )
    if not db_project:
        raise HTTPException(status_code=404, detail="Project not found")
    return db_project


@app.delete("/projects/{project_id}")
def delete_project(project_id: int, db: Session = Depends(get_db)):
    project = crud.delete_project(db=db, project_id=project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return {
        "success": True,
        "message": f"Project with id {project_id} has been deleted.",
    }


@app.post("/documents", response_model=schemas.DocumentResponse)
def create_document(document: schemas.DocumentCreate, db: Session = Depends(get_db)):
    project = crud.get_project_by_id(db=db, project_id=document.project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    return crud.create_document(db=db, document=document)


@app.get(
    "/projects/{project_id}/documents", response_model=list[schemas.DocumentResponse]
)
def list_project_dosuments(project_id: int, db: Session = Depends(get_db)):
    project = crud.get_project_by_id(db=db, project_id=project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    return crud.get_documents_by_project_id(db=db, project_id=project_id)


@app.get("/documents/{document_id}", response_model=schemas.DocumentResponse)
def get_document(document_id: int, db: Session = Depends(get_db)):
    document = crud.get_document_by_id(db=db, document_id=document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    return document


@app.patch("/documents/{document_id}/status", response_model=schemas.DocumentResponse)
def update_document_status(
    document_id: int,
    payload: schemas.StatusUpdate,
    db: Session = Depends(get_db),
):
    document = crud.update_document_status(
        db=db, document_id=document_id, status=payload.status
    )
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    return document


@app.delete("/documents/{document_id}")
def delete_document(document_id: int, db: Session = Depends(get_db)):
    document = crud.delete_document(db=db, document_id=document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    return {
        "success": True,
        "message": f"Document with id {document_id} has been deleted.",
    }


@app.post("/tasks", response_model=schemas.TaskResponse)
def create_task(task: schemas.TaskCreate, db: Session = Depends(get_db)):
    project = crud.get_project_by_id(db=db, project_id=task.project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    return crud.create_task(db=db, task=task)


@app.get("/project/{project_id}/tasks", response_model=list[schemas.TaskResponse])
def list_project_tasks(project_id: int, db: Session = Depends(get_db)):
    project = crud.get_project_by_id(db=db, project_id=project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    return crud.get_tasks_by_project(db=db, project_id=project_id)


@app.patch("/tasks/{task_id}/status", response_model=schemas.TaskResponse)
def update_task_status(
    task_id: int, payload: schemas.TaskStatusUpdate, db: Session = Depends(get_db)
):
    task = crud.update_task_status(db=db, task_id=task_id, status=payload.status)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@app.patch("/tasks/{task_id}/approval", response_model=schemas.TaskResponse)
def update_task_approval(
    task_id: int, payload: schemas.TaskApprovalUpdate, db: Session = Depends(get_db)
):
    task = crud.update_task_approval(db=db, task_id=task_id, approved=payload.approved)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@app.patch("/tasks/{task_id}/priority", response_model=schemas.TaskResponse)
def update_task_priority(
    task_id: int, payload: schemas.TaskPriorityUpdate, db: Session = Depends(get_db)
):
    task = crud.update_task_priority(db=db, task_id=task_id, priority=payload.priority)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@app.delete("/tasks/{task_id}")
def delete_task(task_id: int, db: Session = Depends(get_db)):
    task = crud.delete_task(db=db, task_id=task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"success": True, "message": f"Task with id {task_id} has been deleted."}


@app.get(
    "/projects/{project_id}/chunks", response_model=list[schemas.DocumentChunkResponse]
)
def list_project_chunks(project_id: int, db: Session = Depends(get_db)):
    project = crud.get_project_by_id(db=db, project_id=project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    return crud.get_chunks_by_project(db=db, project_id=project_id)


@app.get(
    "/documents/{document_id}/chunks",
    response_model=list[schemas.DocumentChunkResponse],
)
def list_document_chunks(document_id: int, db: Session = Depends(get_db)):
    document = crud.get_document_by_id(db=db, document_id=document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    return crud.get_chunks_by_document(db=db, document_id=document_id)


@app.post("/audit-logs")
def create_audit_log(audit_log: schemas.AuditLogCreate, db: Session = Depends(get_db)):
    return crud.create_audit_log(db=db, audit_log=audit_log)


@app.get(
    "/projects/{project_id}/audit-logs", response_model=list[schemas.AuditLogResponse]
)
def list_project_audit_logs(project_id: int, db: Session = Depends(get_db)):
    project = crud.get_project_by_id(db=db, project_id=project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    return crud.get_audit_logs_by_project(db=db, project_id=project_id)


@app.post("/ai/test-generate")
def test_generate():
    response = llm_provider.generate("Reply with only: Hello from Ollama.")
    return {
        "provider": llm_provider.provider,
        "model": llm_provider.model,
        "response": response,
    }


@app.get("/ai/embedding-health")
def embedding_health():
    return embedding_provider.health()


@app.post("/ai/test-embed")
def test_embed():
    text = "This is a test document for embedding."
    embedding = embedding_provider.embed(text)
    return {
        "provider": embedding_provider.provider,
        "model": embedding_provider.model,
        "dimension": len(embedding),
        "sample": embedding[:5],  # Show first 5 dimensions as a sample
    }


@app.post(
    "/projects/{project_id}/documents/upload", response_model=schemas.DocumentResponse
)
async def upload_project_document(
    project_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    project = crud.get_project_by_id(db=db, project_id=project_id)

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
        project_id=project_id,
        filename=file.filename,
        filetype=file.content_type,
        storage_path=storage_path,
    )

    document = crud.create_document(db=db, document=document_data)

    return document


@app.post("/documents/{document_id}/process")
def process_document(document_id: int, db: Session = Depends(get_db)):
    document = crud.get_document_by_id(db=db, document_id=document_id)

    if not document:
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
        embedding = embedding_provider.embed(chunk)

        chunk_data = schemas.DocumentChunkCreate(
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

        qdrant_point_id = qdrant_provider.upsert_chunk(
            embedding=embedding,
            project_id=document.project_id,
            document_id=document.id,
            chunk_id=saved_chunk.id,
            chunk_index=index,
            content=chunk,
        )

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


@app.post("/projects/{project_id}/search")
def search_project_documents(
    project_id: int,
    payload: schemas.ProjectSearchRequest,
    db: Session = Depends(get_db),
):
    project = crud.get_project_by_id(db=db, project_id=project_id)

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    query_embedding = embedding_provider.embed(payload.query)

    results = qdrant_provider.search_chunks(
        query_embedding=query_embedding,
        project_id=project_id,
        top_k=payload.top_k,
    )

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
