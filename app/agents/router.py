# app/agents/router.py
import re

from app.agents.state import ShrutiState
from app.services.llm_service import llm


FAQ_TOPICS = (
    "KYC verification, required KYC documents, account balance, "
    "normal transaction status, and eSewa customer support"
)

ESCALATION_PATTERNS = (
    r"\bwrong account\b",
    r"\bsent .*wrong\b",
    r"\btransfer.*wrong\b",
    r"\bpayment.*wrong\b",
    r"\bunauthori[sz]ed\b",
    r"\bfraud\b",
    r"\bscam\b",
    r"\bstolen\b",
    r"\bhacked\b",
    r"\baccount takeover\b",
    r"\bmissing payment\b",
    r"\bdispute\b",
    r"\bchargeback\b",
    r"\bcharged twice\b",
)


def requires_escalation(transcript: str) -> bool:
    normalized_transcript = transcript.lower()

    return any(
        re.search(pattern, normalized_transcript)
        for pattern in ESCALATION_PATTERNS
    )


def router_node(state: ShrutiState) -> ShrutiState:
    transcript = state["transcript"]

    # Financial disputes and security issues should not depend only on
    # probabilistic LLM classification.
    if requires_escalation(transcript):
        return {**state, "route": "escalate"}

    prompt = f"""You are a strict routing classifier for a financial customer-support voice agent.

Choose exactly one route:
- rag
- general
- escalate

The knowledge base can answer only informational questions about:
{FAQ_TOPICS}

Use these rules in order:

1. Choose "escalate" when the user needs investigation, correction, account-specific action,
   or human assistance.

2. Choose "escalate" when the question is unclear or you are not confident that the
   knowledge base contains the answer.

3. Choose "rag" only for informational questions that the knowledge base directly covers,
   such as:
   - how to check an account balance
   - why KYC verification is delayed
   - which documents are needed for KYC
   - normal transaction-status timing

4. Choose "general" only for unrelated general-knowledge questions.

Examples:

Question: How do I check my account balance?
Route: rag

Question: Why is my KYC not verified yet?
Route: rag

Question: How many moons does Jupiter have?
Route: general

Question: My payment went to the wrong account.
Route: escalate

Question: Someone used my account without permission.
Route: escalate

Question: I was charged twice.
Route: escalate

Question: What should I do about a payment problem?
Route: escalate

Return only one word: rag, general, or escalate.

Question: {transcript}
"""

    response = llm.invoke(prompt).content.strip().lower()

    if response not in {"rag", "general", "escalate"}:
        response = "escalate"

    return {**state, "route": response}