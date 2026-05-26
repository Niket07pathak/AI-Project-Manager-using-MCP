import os
import logging
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()
logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set")

engine = create_engine(DATABASE_URL, pool_pre_ping=True)

SQL = """
ALTER TABLE tasks
ALTER COLUMN approved TYPE BOOLEAN
USING
  CASE
    WHEN approved::text IN ('true', 'True', '1', 'yes', 'approved') THEN true
    ELSE false
  END;

ALTER TABLE tasks
ALTER COLUMN approved SET DEFAULT false;

UPDATE tasks
SET approved = true
WHERE status = 'approved';

UPDATE tasks
SET approved = false
WHERE status != 'approved';
"""

def main():
    with engine.begin() as conn:
        conn.execute(text(SQL))

    logger.info("tasks.approved converted to BOOLEAN successfully.")

if __name__ == "__main__":
    main()
