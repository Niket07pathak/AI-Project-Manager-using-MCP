import os
import logging

from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()
logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set in the environment variables.")


TABLES_AND_INDEXES = [
    ("projects", "idx_projects_user_id"),
    ("documents", "idx_documents_user_id"),
    ("document_chunks", "idx_document_chunks_user_id"),
    ("tasks", "idx_tasks_user_id"),
    ("github_issues", "idx_github_issues_user_id"),
    ("audit_logs", "idx_audit_logs_user_id"),
    ("workflow_runs", "idx_workflow_runs_user_id"),
]


def main() -> None:
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)

    with engine.begin() as connection:
        for table_name, index_name in TABLES_AND_INDEXES:
            connection.execute(
                text(
                    f"""
                    ALTER TABLE {table_name}
                    ADD COLUMN IF NOT EXISTS user_id VARCHAR(255)
                    """
                )
            )
            connection.execute(
                text(
                    f"""
                    CREATE INDEX IF NOT EXISTS {index_name}
                    ON {table_name} (user_id)
                    """
                )
            )

    logger.info("Auth user_id columns and indexes are ready.")


if __name__ == "__main__":
    main()
