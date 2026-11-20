import json

import redis

from app.core.settings import settings

redis_client = redis.from_url(settings.redis_url, decode_responses=True)

HISTORY_TTL_SECONDS = 60 * 60 * 24
SESSION_INDEX = "shruti:sessions"


def _history_key(session_id: str) -> str:
    return f"chat:{session_id}"


def get_history(session_id: str) -> list[dict]:
    raw = redis_client.get(_history_key(session_id))
    return json.loads(raw) if raw else []


def append_message(session_id: str, role: str, content: str, route: str | None = None) -> None:
    history = get_history(session_id)
    turn = {"role": role, "content": content}
    if route:
        turn["route"] = route
    history.append(turn)
    redis_client.set(_history_key(session_id), json.dumps(history), ex=HISTORY_TTL_SECONDS)
    if role == "user" and redis_client.zscore(SESSION_INDEX, session_id) is None:
        redis_client.zadd(SESSION_INDEX, {session_id: redis_client.time()[0]})


def list_threads() -> list[dict]:
    session_ids = redis_client.zrevrange(SESSION_INDEX, 0, -1)
    threads = []
    for session_id in session_ids:
        history = get_history(session_id)
        if not history:
            continue
        title = next((turn["content"] for turn in history if turn["role"] == "user"), "New conversation")
        threads.append({
            "thread_id": session_id,
            "title": title[:50],
            "created_at": redis_client.zscore(SESSION_INDEX, session_id),
        })
    return threads


def get_thread_messages(session_id: str) -> list[dict]:
    return [
        {"role": turn["role"], "content": turn["content"], "route": turn.get("route")}
        for turn in get_history(session_id)
    ]


def delete_thread(session_id: str) -> bool:
    removed = redis_client.delete(_history_key(session_id))
    redis_client.zrem(SESSION_INDEX, session_id)
    return bool(removed)
