import json

import redis

from app.core.settings import settings

redis_client = redis.from_url(settings.redis_url, decode_responses=True)

HISTORY_TTL_SECONDS = 60 * 60 * 24
CHAT_INDEX = "shruti:chat:sessions"


def _history_key(session_id: str) -> str:
    return f"chat:{session_id}"


def _meta_key(session_id: str) -> str:
    return f"chatmeta:{session_id}"


def _notebook_index(notebook_id: int) -> str:
    return f"smriti:notebook:{notebook_id}:sessions"


def get_history(session_id: str) -> list[dict]:
    raw = redis_client.get(_history_key(session_id))
    return json.loads(raw) if raw else []


def append_message(
    session_id: str,
    role: str,
    content: str,
    *,
    mode: str,
    notebook_id: int | None = None,
    citations: list[dict] | None = None,
) -> None:
    history = get_history(session_id)
    turn = {"role": role, "content": content}
    if citations:
        turn["citations"] = citations
    history.append(turn)
    redis_client.set(_history_key(session_id), json.dumps(history), ex=HISTORY_TTL_SECONDS)
    redis_client.set(
        _meta_key(session_id),
        json.dumps({"mode": mode, "notebook_id": notebook_id}),
        ex=HISTORY_TTL_SECONDS,
    )
    if role != "user":
        return
    score = redis_client.time()[0]
    if mode == "smriti" and notebook_id is not None:
        redis_client.zadd(_notebook_index(notebook_id), {session_id: score})
    else:
        redis_client.zadd(CHAT_INDEX, {session_id: score})


def _threads_from_index(index: str) -> list[dict]:
    session_ids = redis_client.zrevrange(index, 0, -1)
    threads = []
    for session_id in session_ids:
        history = get_history(session_id)
        if not history:
            redis_client.zrem(index, session_id)
            continue
        title = next((turn["content"] for turn in history if turn["role"] == "user"), "New chat")
        threads.append(
            {
                "thread_id": session_id,
                "title": title[:80],
                "updated_at": redis_client.zscore(index, session_id),
            }
        )
    return threads


def list_chat_threads() -> list[dict]:
    return _threads_from_index(CHAT_INDEX)


def list_notebook_threads(notebook_id: int) -> list[dict]:
    return _threads_from_index(_notebook_index(notebook_id))


def get_thread_messages(session_id: str) -> list[dict]:
    return [
        {
            "role": turn["role"],
            "content": turn["content"],
            "citations": turn.get("citations") or [],
        }
        for turn in get_history(session_id)
    ]


def delete_thread(session_id: str) -> bool:
    raw_meta = redis_client.get(_meta_key(session_id))
    removed = redis_client.delete(_history_key(session_id))
    redis_client.delete(_meta_key(session_id))
    redis_client.zrem(CHAT_INDEX, session_id)
    if raw_meta:
        meta = json.loads(raw_meta)
        notebook_id = meta.get("notebook_id")
        if notebook_id is not None:
            redis_client.zrem(_notebook_index(int(notebook_id)), session_id)
    return bool(removed)


def delete_notebook_threads(notebook_id: int) -> None:
    index = _notebook_index(notebook_id)
    for session_id in redis_client.zrange(index, 0, -1):
        redis_client.delete(_history_key(session_id))
        redis_client.delete(_meta_key(session_id))
    redis_client.delete(index)
