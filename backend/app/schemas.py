from datetime import datetime
from pydantic import BaseModel, Field


class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None


class ProjectResponse(BaseModel):
    id: int
    name: str
    description: str | None = None
    status: str
    created_at: datetime
    updated_at: datetime | None = None

    class Config:
        from_attributes = True


class StatusUpdate(BaseModel):
    status: str = Field(..., min_length=1, max_length=50)


class DocumentCreate(BaseModel):
    project_id: int
    filename: str = Field(..., min_length=1, max_length=255)
    filetype: str | None = None
    storage_path: str | None = None


class DocumentResponse(BaseModel):
    id: int
    project_id: int
    filename: str = Field(..., min_length=1, max_length=255)
    filetype: str | None = None
    storage_path: str | None = None
    status: str
    created_at: datetime
    updated_at: datetime | None = None

    class Config:
        from_attributes = True

class DocumentChunkCreate(BaseModel):
    document_id: int
    project_id: int
    chunk_index: int
    content: str = Field(..., min_length=1)
    qdrant_point_id: str | None = None
    token_count: int | None = None

class DocumentChunkResponse(BaseModel):
    id: int
    document_id: int
    project_id: int
    chunk_index: int
    content: str
    qdrant_point_id: str | None = None
    token_count: int | None = None
    created_at: datetime

    class Config:
        from_attributes = True


class TaskCreate(BaseModel):
    project_id: int
    title: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    priority: str = "medium"
    status: str = "pending_approval"
    approved: bool = False


class TaskResponse(BaseModel):
    id: int
    project_id: int
    title: str
    description: str | None = None
    priority: str
    status: str
    approved: bool
    created_at: datetime
    updated_at: datetime | None = None

    class Config:
        from_attributes = True


class TaskStatusUpdate(BaseModel):
    status: str = Field(..., min_length=1, max_length=50)


class TaskApprovalUpdate(BaseModel):
    approved: bool = False


class TaskPriorityUpdate(BaseModel):
    priority: str = Field(..., min_length=1, max_length=50)


class AuditLogCreate(BaseModel):
    project_id: int | None = None
    action: str
    tool_name: str | None = None
    input_data: str | None = None
    output_data: str | None = None
    status: str = "success"


class AuditLogResponse(BaseModel):
    id: int
    project_id: int | None
    action: str
    tool_name: str | None
    input_data: str | None
    output_data: str | None
    status: str
    created_at: datetime

    class Config:
        from_attributes = True

class ProjectSearchRequest(BaseModel):
    query: str
    top_k: int = 5