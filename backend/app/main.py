from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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


app.include_router(ai.router)
app.include_router(projects.router)
app.include_router(documents.router)
app.include_router(tasks.router)
app.include_router(audit_logs.router)
app.include_router(github.router)
app.include_router(notifications.router)
app.include_router(workflow_runs.router)