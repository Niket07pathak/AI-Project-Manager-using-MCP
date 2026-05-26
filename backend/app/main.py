from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.config import allowed_origins, api_docs_enabled, is_development
from backend.app.database import Base, engine
from backend.app.routes import (
    ai,
    audit_logs,
    documents,
    github,
    notifications,
    projects,
    tasks,
    workflow_runs,
)

Base.metadata.create_all(bind=engine)

docs_enabled = api_docs_enabled()

app = FastAPI(
    title="AI Project Manager API",
    version="0.1.0",
    docs_url="/docs" if docs_enabled else None,
    redoc_url="/redoc" if docs_enabled else None,
    openapi_url="/openapi.json" if docs_enabled else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["Authorization", "Content-Type", "X-Internal-API-Key"],
)


@app.get("/")
def root():
    message = "AI Project Manager API is running."
    if is_development() and docs_enabled:
        message = f"{message} Use /docs for API documentation."
    return {
        "message": message
    }


app.include_router(ai.router)
app.include_router(projects.router)
app.include_router(documents.router)
app.include_router(tasks.router)
app.include_router(audit_logs.router)
app.include_router(github.router)
app.include_router(notifications.router)
app.include_router(workflow_runs.router)
