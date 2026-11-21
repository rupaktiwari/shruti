def format_context(hits: list[dict]) -> tuple[str, list[dict]]:
    """Turn retrieved chunks into a prompt block and a de-duplicated citation list."""
    blocks: list[str] = []
    citations: list[dict] = []
    seen: set[tuple[int, int]] = set()
    for hit in hits:
        filename = hit["filename"]
        chunk_index = int(hit["chunk_index"])
        document_id = int(hit["document_id"])
        blocks.append(f"[{filename} #{chunk_index}]\n{hit['text']}")
        key = (document_id, chunk_index)
        if key in seen:
            continue
        seen.add(key)
        citations.append(
            {
                "document_id": document_id,
                "filename": filename,
                "chunk_index": chunk_index,
            }
        )
    return "\n\n".join(blocks), citations
