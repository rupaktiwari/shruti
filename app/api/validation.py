import re

from fastapi import HTTPException

_SESSION = re.compile(r"^[A-Za-z0-9_-]{1,80}$")


def require_session_id(session_id: str) -> str:
    if not _SESSION.fullmatch(session_id or ""):
        raise HTTPException(
            status_code=400,
            detail="session_id must be 1-80 characters: letters, numbers, _ or -",
        )
    return session_id


def require_message(message: str) -> str:
    cleaned = (message or "").strip()
    if not cleaned:
        raise HTTPException(status_code=400, detail="Message is empty")
    if len(cleaned) > 8000:
        raise HTTPException(status_code=400, detail="Message is longer than 8000 characters")
    return cleaned
