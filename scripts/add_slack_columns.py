import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set in .env")

engine = create_engine(DATABASE_URL, pool_pre_ping=True)

SQL = """
ALTER TABLE projects
ADD COLUMN IF NOT EXISTS slack_channel_id VARCHAR(255);

ALTER TABLE projects
ADD COLUMN IF NOT EXISTS slack_channel_name VARCHAR(255);
"""

def main():
    with engine.begin() as conn:
        conn.execute(text(SQL))

    print("Slack columns added successfully.")

if __name__ == "__main__":
    main()
    