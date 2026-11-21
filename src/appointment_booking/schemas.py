import re

from pydantic import BaseModel, ConfigDict, Field, field_validator

NAME_PATTERN = re.compile(r"^[А-Яа-яЁёA-Za-z\s-]+$")


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
