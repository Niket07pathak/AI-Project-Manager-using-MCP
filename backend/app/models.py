
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean
from sqlalchemy.sql import func

from backend.app.database import Base


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(255), nullable=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(50), nullable=False, default="created")

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    github_repo_owner = Column(String(255), nullable=True)
    github_repo_name = Column(String(255), nullable=True)

    slack_channel_id = Column(String(255), nullable=True)
    slack_channel_name = Column(String(255), nullable=True)


class Document(Base):
    __tablename__ = "documents"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(255), nullable=True, index=True)

    project_id = Column(Integer, nullable=False, index=True)

    filename = Column(String(255), nullable=False)
    filetype = Column(String(50), nullable=True)
    storage_path = Column(String(255), nullable=True)

    status = Column(String(50), nullable=False, default="uploaded")

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(255), nullable=True, index=True)
    document_id = Column(Integer, nullable=False, index=True)
    project_id = Column(Integer, nullable=False, index=True)

    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)

    qdrant_point_id = Column(String(255), nullable=True)
    token_count = Column(Integer, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(255), nullable=True, index=True)
    project_id = Column(Integer, nullable=False, index=True)

    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    priority = Column(String(50), nullable=False, default="medium")
    status = Column(String(50), nullable=False, default="pending_approval")

    approved = Column(Boolean, nullable=False, default=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(255), nullable=True, index=True)
    project_id = Column(Integer, nullable=True, index=True)

    action = Column(String(255), nullable=False)
    tool_name = Column(String(255), nullable=True)

    input_data = Column(Text, nullable=True)
    output_data = Column(Text, nullable=True)

    status = Column(String(50), nullable=False, default="success")

    created_at = Column(DateTime(timezone=True), server_default=func.now())

class GitHubIssue(Base):
    __tablename__ = "github_issues"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(255), nullable=True, index=True)
    project_id = Column(Integer, nullable=False, index=True)
    task_id = Column(Integer, nullable=False, index=True)

    issue_number = Column(Integer, nullable=False)
    issue_url = Column(String(500), nullable=False)
    title = Column(String(255), nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())


class WorkflowRun(Base):
    __tablename__ = "workflow_runs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(255), nullable=True, index=True)
    project_id = Column(Integer, nullable=False, index=True)

    workflow_type = Column(String(100), nullable=False)
    status = Column(String(50), nullable=False, default="running")

    input_data = Column(Text, nullable=True)
    output_data = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)

    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
