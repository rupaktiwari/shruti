import json

from app.db.models import Reservation
from app.db.postgres import SessionLocal
from app.schemas.booking import BookingDetails
from app.services.booking_rules import (
    ROOM_CAPACITY,
    ROOM_INVENTORY,
    normalize_room_type,
    parse_iso_date,
    stays_overlap,
)
from app.services.llm_service import llm

EXTRACTION_PROMPT = """You extract hotel reservation details for Himalaya House, a resort in Pokhara.

Conversation so far:
{conversation}

Decide wants_booking from the user's most recent message only.
Set it to true when that message asks to book, asks if a room is free on specific dates, or supplies reservation details for a booking still in progress.
Set it to false when that message is a general question, a policy question, or a complaint — even if a booking was completed earlier in this chat.

Fill name, email, check_in, check_out, guests, and room_type from the whole conversation, not only the latest message.

Dates must be YYYY-MM-DD when you can tell the calendar date. Otherwise use null.
room_type must be "standard", "deluxe", "suite", or null.
guests must be an integer or null.

Respond ONLY with JSON:
{{"wants_booking": true or false, "name": string or null, "email": string or null, "check_in": string or null, "check_out": string or null, "guests": integer or null, "room_type": string or null}}
"""


def _parse_json(text: str) -> dict:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
    return json.loads(cleaned)


def extract_booking_intent(conversation_text: str) -> dict:
    response = llm.invoke(EXTRACTION_PROMPT.format(conversation=conversation_text))
    empty = {
        "wants_booking": False,
        "name": None,
        "email": None,
        "check_in": None,
        "check_out": None,
        "guests": None,
        "room_type": None,
    }
    try:
        parsed = _parse_json(response.content)
    except (json.JSONDecodeError, AttributeError):
        return empty
    parsed["room_type"] = normalize_room_type(parsed.get("room_type"))
    return parsed


def slots_left(room_type: str, check_in: str, check_out: str) -> int | None:
    start = parse_iso_date(check_in)
    end = parse_iso_date(check_out)
    if room_type not in ROOM_INVENTORY or start is None or end is None or end <= start:
        return None

    db = SessionLocal()
    try:
        rows = db.query(Reservation).filter(Reservation.room_type == room_type).all()
        used = 0
        for row in rows:
            other_in = parse_iso_date(row.check_in)
            other_out = parse_iso_date(row.check_out)
            if other_in and other_out and stays_overlap(start, end, other_in, other_out):
                used += 1
        return ROOM_INVENTORY[room_type] - used
    finally:
        db.close()


def save_booking(details: BookingDetails) -> str:
    """Return created, duplicate, unavailable, or invalid."""
    start = parse_iso_date(details.check_in)
    end = parse_iso_date(details.check_out)
    room_type = normalize_room_type(details.room_type)
    if start is None or end is None or end <= start or room_type is None:
        return "invalid"
    if details.guests > ROOM_CAPACITY[room_type]:
        return "invalid"

    db = SessionLocal()
    try:
        existing = (
            db.query(Reservation)
            .filter(
                Reservation.email == details.email,
                Reservation.check_in == start.isoformat(),
                Reservation.check_out == end.isoformat(),
            )
            .first()
        )
        if existing:
            return "duplicate"

        remaining = slots_left(room_type, start.isoformat(), end.isoformat())
        if remaining is None or remaining <= 0:
            return "unavailable"

        db.add(
            Reservation(
                name=details.name,
                email=str(details.email),
                check_in=start.isoformat(),
                check_out=end.isoformat(),
                guests=details.guests,
                room_type=room_type,
            )
        )
        db.commit()
        return "created"
    finally:
        db.close()
