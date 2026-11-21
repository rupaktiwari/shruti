from app.services.context import format_context
from app.services.embedding_service import embed_query
from app.services.vector_store_service import count_notebook_points, search


def retrieve(question: str, notebook_id: int, top_k: int = 5) -> tuple[str, list[dict], int]:
    point_count = count_notebook_points(notebook_id)
    if point_count == 0:
        return "", [], 0
    context, citations = format_context(search(embed_query(question), notebook_id, top_k=top_k))
    return context, citations, point_count
