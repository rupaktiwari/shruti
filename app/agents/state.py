# app/agents/state.py
from typing import TypedDict, Literal, Optional

class ShrutiState(TypedDict):
    transcript: str
    thread_id: str
    route: Optional[Literal["rag", "general", "escalate"]]
    confidence: Optional[float]
    answer: Optional[str]