import uuid

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchValue,
    PointStruct,
    VectorParams,
)

from app.core.settings import settings

COLLECTION_NAME = "documents"
VECTOR_SIZE = 384

client = QdrantClient(url=settings.qdrant_url)


def ensure_collection() -> None:
    existing = [collection.name for collection in client.get_collections().collections]
    if COLLECTION_NAME not in existing:
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE),
        )


def upsert_chunks(
    document_id: int,
    filename: str,
    chunks: list[str],
    embeddings: list[list[float]],
    source: str = "upload",
) -> None:
    points = [
        PointStruct(
            id=str(uuid.uuid4()),
            vector=embedding,
            payload={
                "document_id": document_id,
                "filename": filename,
                "chunk_index": index,
                "text": chunk,
                "source": source,
            },
        )
        for index, (chunk, embedding) in enumerate(zip(chunks, embeddings))
    ]
    client.upsert(collection_name=COLLECTION_NAME, points=points)


def search(query_embedding: list[float], top_k: int = 3) -> list[str]:
    results = client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_embedding,
        limit=top_k,
    )
    return [point.payload["text"] for point in results.points if point.payload]


def count_seed_points() -> int:
    result = client.count(
        collection_name=COLLECTION_NAME,
        count_filter=Filter(
            must=[FieldCondition(key="source", match=MatchValue(value="seed"))]
        ),
        exact=True,
    )
    return result.count


def delete_seed_points() -> None:
    client.delete(
        collection_name=COLLECTION_NAME,
        points_selector=Filter(
            must=[FieldCondition(key="source", match=MatchValue(value="seed"))]
        ),
    )
