from typing import Literal, Optional, TypedDict


class TurnState(TypedDict):
    mode: Literal["shruti", "smriti"]
    transcript: str
    session_id: str
    notebook_id: Optional[int]
    history: list[dict]
    route: Optional[Literal["chat", "answer", "empty"]]
    context: Optional[str]
    citations: list[dict]
    answer: Optional[str]
