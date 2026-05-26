import os
import logging
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()
logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set in .env")

engine = create_engine(DATABASE_URL, pool_pre_ping=True)

ALTER_QUERIES = [
    """
    ALTER TABLE projects
    ADD COLUMN IF NOT EXISTS github_repo_owner VARCHAR(255);
    """,
    """
    ALTER TABLE projects
    ADD COLUMN IF NOT EXISTS github_repo_name VARCHAR(255);
    """,
]

def main():
    with engine.begin() as conn:
        for query in ALTER_QUERIES:
            conn.execute(text(query))

    logger.info("GitHub repo columns added successfully.")

if __name__ == "__main__":
    main()
