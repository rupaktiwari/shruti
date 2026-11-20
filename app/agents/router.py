import re

from app.agents.state import ShrutiState
from app.services.llm_service import llm

FAQ_TOPICS = (
    "Himalaya House rooms and rates, check-in and check-out, cancellation, "
    "dining hours, pool, spa, wifi, airport pickup, and Pokhara location"
)

ESCALATION_PATTERNS = (
    r"\brefund\b",
    r"\bovercharg",
    r"\bcharged twice\b",
    r"\bmanager\b",
    r"\bcomplaint\b",
    r"\bstolen\b",
    r"\bfraud\b",
    r"\binjur",
    r"\bemergency\b",
    r"\bunsafe\b",
    r"\bdirty room\b",
    r"फिर्ता",
    r"गुनासो",
    r"प्रबन्धक",
)


def requires_escalation(transcript: str) -> bool:
    normalized = transcript.lower()
    return any(re.search(pattern, normalized) for pattern in ESCALATION_PATTERNS)


def router_node(state: ShrutiState) -> ShrutiState:
    transcript = state["transcript"]
    if requires_escalation(transcript):
        return {**state, "route": "escalate"}

    recent = state.get("history") or []
    recent_text = "\n".join(
        f"{turn['role']}: {turn['content']}" for turn in recent[-4:]
    )

    prompt = f"""You are a strict routing classifier for Shruti, the concierge at Himalaya House resort in Pokhara.

Choose exactly one route:
- booking
- rag
- general
- escalate

The knowledge base covers only:
{FAQ_TOPICS}

Use the recent conversation only to tell whether the latest message continues a reservation.
Decide from the latest guest message.

Rules, in order:
1. escalate — the guest needs a human: refund, billing dispute, safety, injury, theft, a complaint, or a manager.
2. booking — the guest wants to reserve a room, is asking if a specific room type is free on dates, or is supplying name, email, dates, guests, or room type for a reservation in progress.
3. rag — an informational question the knowledge base covers: rates, policies, dining, amenities, location.
4. general — anything else, including chit-chat and questions unrelated to the resort.

Examples:
Guest: What time is check-in?
Route: rag

Guest: How much is a deluxe room?
Route: rag

Guest: Book a suite for two from 2026-12-12 to 2026-12-15.
Route: booking

Guest: My email is ram@example.com
Route: booking

Guest: How many moons does Jupiter have?
Route: general

Guest: I want a refund, I was charged twice.
Route: escalate

Recent conversation:
{recent_text}

Latest guest message: {transcript}

Return only one word: booking, rag, general, or escalate.
"""
    response = llm.invoke(prompt).content.strip().lower()
    if response not in {"booking", "rag", "general", "escalate"}:
        response = "escalate"
    return {**state, "route": response}
