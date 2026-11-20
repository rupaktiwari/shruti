from pydantic import BaseModel, EmailStr, Field


class BookingDetails(BaseModel):
    name: str
    email: EmailStr
    check_in: str
    check_out: str
    guests: int = Field(ge=1, le=8)
    room_type: str
