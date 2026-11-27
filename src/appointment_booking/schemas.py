from datetime import datetime
import re

from pydantic import BaseModel, ConfigDict, Field, field_validator

from appointment_booking.models import SlotStatus

NAME_PATTERN = re.compile(r"^[А-Яа-яЁёA-Za-z\s-]+$")
PHONE_CLEAN_PATTERN = re.compile(r"[\s()\-]+")
PHONE_PATTERN = re.compile(r"^\+[1-9]\d{7,14}$")


class DoctorCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    specialty: str = Field(min_length=2, max_length=100)

    @field_validator("name", "specialty")
    @classmethod
    def validate_text_field(cls, value: str) -> str:
        cleaned = value.strip()
        if len(cleaned) < 2:
            raise ValueError("Значение не может быть пустым или короче 2 символов")
        if not NAME_PATTERN.fullmatch(cleaned):
            raise ValueError("Допустимы только буквы, пробелы и дефис")
        return cleaned


class DoctorRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    doctor_id: int
    name: str
    specialty: str


class BookingCreate(BaseModel):
    slot_id: int
    service_id: int
    patient_name: str = Field(min_length=2, max_length=100)
    telephone: str
    email: str | None = None
    telegram_id: str | None = None

    @field_validator("patient_name")
    @classmethod
    def validate_patient_name(cls, value: str) -> str:
        cleaned = value.strip()
        if len(cleaned) < 2:
            raise ValueError("Name must be at least 2 characters long")
        if not NAME_PATTERN.fullmatch(cleaned):
            raise ValueError("Only letters, spaces, and hyphens are allowed")
        return cleaned

    @field_validator("telephone")
    @classmethod
    def validate_telephone(cls, value: str) -> str:
        cleaned = PHONE_CLEAN_PATTERN.sub("", value.strip())
        if not PHONE_PATTERN.fullmatch(cleaned):
            raise ValueError(
                "Telephone must be in international E.164 format (e.g., +905551234567)"
            )
        return cleaned

    @field_validator("email", "telegram_id")
    @classmethod
    def empty_string_to_none(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned if cleaned else None


class BookingRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    slot_id: int
    doctor_id: int
    service_id: int
    patient_id: int
    room_number: str
    start_time: datetime
    end_time: datetime
    status: SlotStatus
