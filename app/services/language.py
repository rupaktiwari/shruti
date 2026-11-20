def prefers_nepali(text: str) -> bool:
    return any("\u0900" <= char <= "\u097f" for char in text)
