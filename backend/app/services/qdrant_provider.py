import os
import logging
from uuid import uuid4
from dotenv import load_dotenv

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
    PayloadSchemaType,
)
from backend.app.services.errors import ServiceError

load_dotenv()
logger = logging.getLogger(__name__)


class QdrantProvider:
    def __init__(self):
        self.url = os.getenv("QDRANT_URL")
        self.api_key = os.getenv("QDRANT_API_KEY")
        self.collection_name = os.getenv("QDRANT_COLLECTION")
        self.vector_size = int(os.getenv("QDRANT_VECTOR_SIZE", "384"))

        if not self.url or not self.api_key or not self.collection_name:
            raise RuntimeError(
                "Qdrant configuration is missing in environment variables."
            )
        self.client = QdrantClient(
            url=self.url,
            api_key=self.api_key,
            timeout=30,
        )
        self._collection_ready = False

    def _ensure_ready(self):
        if self._collection_ready:
            return
        self.ensure_collection()
        self._collection_ready = True

    def ensure_collection(self):
        try:
            collections = self.client.get_collections().collections
            existing_names = [collection.name for collection in collections]
        except Exception as exc:
            logger.warning("Failed to list Qdrant collections: %s", exc)
            raise ServiceError(
                "SERVICE_UNAVAILABLE",
                "qdrant",
                "Could not connect to Qdrant collections.",
            ) from exc

        if self.collection_name not in existing_names:
            try:
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=self.vector_size,
                        distance=Distance.COSINE,
                    ),
                )
            except Exception as exc:
                logger.warning("Failed to create Qdrant collection: %s", exc)
                raise ServiceError(
                    "BAD_RESPONSE",
                    "qdrant",
                    "Could not create Qdrant collection.",
                ) from exc
        try:
            self.client.create_payload_index(
                collection_name=self.collection_name,
                field_name="project_id",
                field_schema=PayloadSchemaType.INTEGER,
            )
        except Exception:
            pass

    def upsert_chunk(
        self,
        embedding: list[float],
        project_id: int,
        document_id: int,
        chunk_id: int,
        chunk_index: int,
        content: str,
    ) -> str:
        point_id = str(uuid4())
        self._ensure_ready()

        point = PointStruct(
            id=point_id,
            vector=embedding,
            payload={
                "project_id": project_id,
                "document_id": document_id,
                "chunk_id": chunk_id,
                "chunk_index": chunk_index,
                "content": content,
            },
        )
        try:
            self.client.upsert(
                collection_name=self.collection_name,
                points=[point],
            )
        except Exception as exc:
            logger.warning("Qdrant upsert failed for project %s: %s", project_id, exc)
            raise ServiceError(
                "BAD_RESPONSE",
                "qdrant",
                "Could not store document chunk in Qdrant.",
            ) from exc
        return point_id

    def search_chunks(self, query_embedding: list[float], project_id: int, top_k: int = 5):
        self._ensure_ready()
        try:
            results = self.client.query_points(
                collection_name=self.collection_name,
                query=query_embedding,
                query_filter=Filter(
                    must=[
                        FieldCondition(
                            key="project_id",
                            match=MatchValue(value=project_id),
                        )
                    ]
                ),
                limit=top_k,
                with_payload=True,
                timeout=30,
            )
        except Exception as exc:
            logger.warning("Qdrant search failed for project %s: %s", project_id, exc)
            raise ServiceError(
                "BAD_RESPONSE",
                "qdrant",
                "Could not search project documents in Qdrant.",
            ) from exc

        return results.points


qdrant_provider = QdrantProvider()
