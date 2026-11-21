import uuid

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    IsNullCondition,
    MatchValue,
    PayloadField,
    PayloadSchemaType,
    PointStruct,
    VectorParams,
)

from app.core.logging_config import get_logger
from app.core.settings import settings

logger = get_logger(__name__)

COLLECTION_NAME = "documents"
VECTOR_SIZE = 384

client = QdrantClient(url=settings.qdrant_url)


def _notebook_filter(notebook_id: int) -> Filter:
    return Filter(
        must=[FieldCondition(key="notebook_id", match=MatchValue(value=notebook_id))]
    )


def ensure_collection() -> None:
    existing = [collection.name for collection in client.get_collections().collections]
    if COLLECTION_NAME not in existing:
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE),
        )
    try:
        client.create_payload_index(
            collection_name=COLLECTION_NAME,
            field_name="notebook_id",
            field_schema=PayloadSchemaType.INTEGER,
        )
    except Exception:
        logger.debug("notebook_id payload index already present")
    delete_unscoped_points()


def delete_unscoped_points() -> None:
    """Remove vectors left by the old global knowledge base, which had no notebook."""
    client.delete(
        collection_name=COLLECTION_NAME,
        points_selector=Filter(
            must=[IsNullCondition(is_null=PayloadField(key="notebook_id"))]
        ),
    )


def upsert_chunks(
    notebook_id: int,
    document_id: int,
    filename: str,
    chunks: list[str],
    embeddings: list[list[float]],
) -> None:
    points = [
        PointStruct(
            id=str(uuid.uuid4()),
            vector=embedding,
            payload={
                "notebook_id": notebook_id,
                "document_id": document_id,
                "filename": filename,
                "chunk_index": index,
                "text": chunk,
            },
        )
        for index, (chunk, embedding) in enumerate(zip(chunks, embeddings))
    ]
    if points:
        client.upsert(collection_name=COLLECTION_NAME, points=points)


def search(query_embedding: list[float], notebook_id: int, top_k: int = 5) -> list[dict]:
    results = client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_embedding,
        query_filter=_notebook_filter(notebook_id),
        limit=top_k,
    )
    hits = []
    for point in results.points:
        payload = point.payload or {}
        if "text" not in payload:
            continue
        hits.append(
            {
                "document_id": payload.get("document_id"),
                "filename": payload.get("filename") or "document",
                "chunk_index": payload.get("chunk_index", 0),
                "text": payload["text"],
            }
        )
    return hits


def count_notebook_points(notebook_id: int) -> int:
    result = client.count(
        collection_name=COLLECTION_NAME,
        count_filter=_notebook_filter(notebook_id),
        exact=True,
    )
    return result.count


def delete_document_points(document_id: int) -> None:
    client.delete(
        collection_name=COLLECTION_NAME,
        points_selector=Filter(
            must=[FieldCondition(key="document_id", match=MatchValue(value=document_id))]
        ),
    )


def delete_notebook_points(notebook_id: int) -> None:
    client.delete(
        collection_name=COLLECTION_NAME,
        points_selector=_notebook_filter(notebook_id),
    )
