import os
from uuid import uuid4
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()


class StorageProvider:
    def __init__(self):
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.service_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        self.bucket = os.getenv("SUPABASE_BUCKET")

        if not self.supabase_url or not self.service_key or not self.bucket:
            raise RuntimeError(
                "Supabase configuration is missing in environment variables."
            )

        self.client: Client = create_client(
            self.supabase_url,
            self.service_key
        )

    def upload_file(
        self,
        project_id: int,
        filename: str,
        file_bytes: bytes,
        content_type: str | None = None,
    ) -> str:
        safe_filename = filename.replace(" ", "_")
        unique_name = f"{uuid4()}_{safe_filename}"
        storage_path = f"projects/{project_id}/documents/{unique_name}"

        self.client.storage.from_(self.bucket).upload(
            path=storage_path,
            file=file_bytes,
            file_options={
                "content-type": content_type or "application/octet-stream",
                "upsert": "false",
            },
        )

        return storage_path


storage_provider = StorageProvider()