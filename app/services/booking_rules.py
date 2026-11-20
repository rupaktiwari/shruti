from datetime import date

ROOM_INVENTORY = {
    "standard": 8,
    "deluxe": 5,
    "suite": 2,
}

ROOM_CAPACITY = {
    "standard": 2,
    "deluxe": 3,
    "suite": 4,
}

REQUIRED_FIELDS = ("name", "email", "check_in", "check_out", "guests", "room_type")


def normalize_room_type(value: str | None) -> str | None:
    if not value:
        return None
    lowered = value.strip().lower()
    for room_type in ROOM_INVENTORY:
        if room_type in lowered:
            return room_type
    return None


def parse_iso_date(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(str(value).strip()[:10])
    except ValueError:
        return None


def stays_overlap(check_in: date, check_out: date, other_in: date, other_out: date) -> bool:
    return check_in < other_out and other_in < check_out
