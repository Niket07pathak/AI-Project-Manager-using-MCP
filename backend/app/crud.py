from sqlalchemy.orm import Session
from backend.app import models, schemas


def create_project(db: Session, project: schemas.ProjectCreate):
    db_project = models.Project(
        name=project.name,
        description=project.description,
        github_repo_owner=project.github_repo_owner,
        github_repo_name=project.github_repo_name,
        slack_channel_id=project.slack_channel_id,
        slack_channel_name=project.slack_channel_name,
    )
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project


def get_project(db: Session):
    return db.query(models.Project).order_by(models.Project.created_at.desc()).all()


def get_project_by_id(db: Session, project_id: int):
    return db.query(models.Project).filter(models.Project.id == project_id).first()


def update_project_status(db: Session, project_id: int, status: str):
    de_project = get_project_by_id(db, project_id)
    if not de_project:
        return None
    de_project.status = status
    db.commit()
    db.refresh(de_project)
    return de_project


def delete_project(db: Session, project_id: int):
    db_project = get_project_by_id(db, project_id)
    if not db_project:
        return None

    db.delete(db_project)
    db.commit()
    return db_project


def create_document(db: Session, document: schemas.DocumentCreate):
    db_document = models.Document(
        project_id=document.project_id,
        filename=document.filename,
        filetype=document.filetype,
        storage_path=document.storage_path,
    )
    db.add(db_document)
    db.commit()
    db.refresh(db_document)
    return db_document


def get_documents_by_project_id(db: Session, project_id: int):
    return (
        db.query(models.Document)
        .filter(models.Document.project_id == project_id)
        .order_by(models.Document.created_at.desc())
        .all()
    )


def get_document_by_id(db: Session, document_id: int):
    return db.query(models.Document).filter(models.Document.id == document_id).first()


def update_document_status(db: Session, document_id: int, status: str):
    db_document = get_document_by_id(db, document_id)
    if not db_document:
        return None
    db_document.status = status
    db.commit()
    db.refresh(db_document)
    return db_document


def delete_document(db: Session, document_id: int):
    db_document = get_document_by_id(db, document_id)
    if not db_document:
        return None

    db.delete(db_document)
    db.commit()
    return db_document


def create_document_chunk(db: Session, document_chunk: schemas.DocumentChunkCreate):
    db_chunk = models.DocumentChunk(
        document_id=document_chunk.document_id,
        project_id=document_chunk.project_id,
        chunk_index=document_chunk.chunk_index,
        content=document_chunk.content,
        qdrant_point_id=document_chunk.qdrant_point_id,
        token_count=document_chunk.token_count,
    )
    db.add(db_chunk)
    db.commit()
    db.refresh(db_chunk)
    return db_chunk


def get_chunks_by_document(db: Session, document_id: int):
    return (
        db.query(models.DocumentChunk)
        .filter(models.DocumentChunk.document_id == document_id)
        .order_by(models.DocumentChunk.chunk_index.asc())
        .all()
    )


def get_chunks_by_project(db: Session, project_id: int):
    return (
        db.query(models.DocumentChunk)
        .filter(models.DocumentChunk.project_id == project_id)
        .order_by(models.DocumentChunk.created_at.desc())
        .all()
    )


def create_task(db: Session, task: schemas.TaskCreate):
    db_task = models.Task(
        project_id=task.project_id,
        title=task.title,
        description=task.description,
        priority=task.priority,
        status=task.status,
        approved=task.approved,
    )
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task


def get_tasks_by_project(db: Session, project_id: int):
    return (
        db.query(models.Task)
        .filter(models.Task.project_id == project_id)
        .order_by(models.Task.created_at.desc())
        .all()
    )


def get_task_by_id(db: Session, task_id: int):
    return db.query(models.Task).filter(models.Task.id == task_id).first()


def update_task_status(db: Session, task_id: int, status: str):
    db_task = get_task_by_id(db, task_id)
    if not db_task:
        return None
    db_task.status = status
    db.commit()
    db.refresh(db_task)
    return db_task


def update_task_approval(db: Session, task_id: int, approved: bool):
    db_task = get_task_by_id(db, task_id)
    if not db_task:
        return None
    db_task.approved = approved
    db.commit()
    db.refresh(db_task)
    return db_task


def update_task_priority(db: Session, task_id: int, priority: str):
    db_task = get_task_by_id(db, task_id)
    if not db_task:
        return None
    db_task.priority = priority
    db.commit()
    db.refresh(db_task)
    return db_task


def delete_task(db: Session, task_id: int):
    db_task = get_task_by_id(db, task_id)
    if not db_task:
        return None

    db.delete(db_task)
    db.commit()
    return db_task


def create_audit_log(db: Session, audit_log: schemas.AuditLogCreate):
    db_audit_log = models.AuditLog(
        project_id=audit_log.project_id,
        action=audit_log.action,
        tool_name=audit_log.tool_name,
        input_data=audit_log.input_data,
        output_data=audit_log.output_data,
        status=audit_log.status,
    )

    db.add(db_audit_log)
    db.commit()
    db.refresh(db_audit_log)

    return db_audit_log


def get_audit_logs_by_project(db: Session, project_id: int):
    return (
        db.query(models.AuditLog)
        .filter(models.AuditLog.project_id == project_id)
        .order_by(models.AuditLog.created_at.desc())
        .all()
    )


def edit_task(db: Session, task_id: int, payload: schemas.TaskEditUpdate):
    db_task = get_task_by_id(db, task_id)

    if not db_task:
        return None

    if payload.title is not None:
        db_task.title = payload.title

    if payload.description is not None:
        db_task.description = payload.description

    if payload.priority is not None:
        db_task.priority = payload.priority

    db.commit()
    db.refresh(db_task)

    return db_task


def approve_task(db: Session, task_id: int):
    db_task = get_task_by_id(db, task_id)

    if not db_task:
        return None

    db_task.approved = True
    db_task.status = "approved"

    db.commit()
    db.refresh(db_task)

    return db_task


def reject_task(db: Session, task_id: int):
    db_task = get_task_by_id(db, task_id)

    if not db_task:
        return None

    db_task.approved = False
    db_task.status = "rejected"

    db.commit()
    db.refresh(db_task)

    return db_task


def get_approved_tasks_by_project(db: Session, project_id: int):
    return (
        db.query(models.Task)
        .filter(models.Task.project_id == project_id)
        .filter(models.Task.approved == True)
        .filter(models.Task.status == "approved")
        .all()
    )


def create_github_issue_record(db: Session, issue: schemas.GitHubIssueCreate):
    db_issue = models.GitHubIssue(
        project_id=issue.project_id,
        task_id=issue.task_id,
        issue_number=issue.issue_number,
        issue_url=issue.issue_url,
        title=issue.title,
    )

    db.add(db_issue)
    db.commit()
    db.refresh(db_issue)

    return db_issue


def get_github_issues_by_project(db: Session, project_id: int):
    return (
        db.query(models.GitHubIssue)
        .filter(models.GitHubIssue.project_id == project_id)
        .order_by(models.GitHubIssue.created_at.desc())
        .all()
    )
