from datetime import date

from app.core.logging_config import get_logger
from app.core.settings import settings
from app.services.language import prefers_nepali
from app.services.llm_service import llm

logger = get_logger(__name__)


def escalate(transcript: str, session_id: str) -> str:
    ticket_prompt = f"""Extract a short front-desk ticket.
Respond in exactly this format:

Issue: <one line>
Date: {date.today().isoformat()}
Contact: {settings.front_desk_email}

Guest message: {transcript}"""
    ticket = llm.invoke(ticket_prompt).content
    logger.info("[ESCALATION TICKET] session=%s\n%s", session_id, ticket)

    if prefers_nepali(transcript):
        return (
            "यो कुरा म आफैं समाधान गर्न सक्दिनँ। "
            "तपाईंको सन्देश हिमालया हाउसको फ्रन्ट डेस्कमा पठाइएको छ।"
        )
    return (
        "I can't resolve that myself. "
        "I've passed your message to the Himalaya House front desk."
    )
