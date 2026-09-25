# app/services/escalation_service.py
from datetime import date
from app.services.llm_service import llm
from app.core.settings import settings
from app.core.logging_config import get_logger

logger = get_logger(__name__)

def escalate(transcript: str, thread_id: str) -> str:
    extraction_prompt = f'''Extract a structured support ticket from this user query.
Respond in exactly this format, nothing else:

Issue: <one-line summary of the problem>
Date: {date.today().isoformat()}
Contact: {settings.gmail_address}

User query: {transcript}'''

    ticket = llm.invoke(extraction_prompt).content

    # Prototype mode — swap this for real smtplib sending later
    logger.info("[ESCALATION TICKET] thread=%s\n%s", thread_id, ticket)

    return (
    "म यस प्रश्नको विश्वसनीय उत्तर फेला पार्न सकिनँ। "
    "तपाईंको प्रश्न मानव प्रतिनिधिकहाँ पठाइएको छ।"
) 