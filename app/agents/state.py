from typing import Literal, Optional, TypedDict


class ShrutiState(TypedDict):
    transcript: str
    session_id: str
    history: list[dict]
    route: Optional[Literal["rag", "booking", "general", "escalate"]]
    answer: Optional[str]
