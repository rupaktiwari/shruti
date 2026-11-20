from app.services.embedding_service import embed_query
from app.services.vector_store_service import search


def retrieve(question: str, top_k: int = 5) -> str | None:
    chunks = search(embed_query(question), top_k=top_k)
    if not chunks:
        return None
    return "\n\n".join(chunks)
