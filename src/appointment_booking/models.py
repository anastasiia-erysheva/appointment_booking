from datetime import datetime
import enum

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from appointment_booking.database import Base


class GenderType(str, enum.Enum):
    male = "male"
    female = "female"


class Patient(Base):
    __tablename__ = "patients"

    patient_id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    gender: Mapped[GenderType | None] = mapped_column(
        Enum(GenderType, name="gender_type"), nullable=True
    )
    email: Mapped[str | None] = mapped_column(String, unique=True, nullable=True)
    telephone: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    telegram_id: Mapped[str | None] = mapped_column(String, unique=True, nullable=True)


class Doctor(Base):
    __tablename__ = "doctors"

    doctor_id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    specialty: Mapped[str] = mapped_column(String, nullable=False)


class Service(Base):
    __tablename__ = "services"

    service_id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    duration_minutes: Mapped[int] = mapped_column(nullable=False)
    price: Mapped[int] = mapped_column(nullable=False)


class DoctorService(Base):
    __tablename__ = "doctor_services"

    doctor_service_id: Mapped[int] = mapped_column(primary_key=True)
    doctor_id: Mapped[int] = mapped_column(
        ForeignKey("doctors.doctor_id"), nullable=False
    )
    service_id: Mapped[int] = mapped_column(
        ForeignKey("services.service_id"), nullable=False
    )


class Slot(Base):
    __tablename__ = "slots"

    slot_id: Mapped[int] = mapped_column(primary_key=True)
    doctor_id: Mapped[int] = mapped_column(
        ForeignKey("doctors.doctor_id"), nullable=False
    )
    service_id: Mapped[int | None] = mapped_column(
        ForeignKey("services.service_id"), nullable=True
    )
    patient_id: Mapped[int | None] = mapped_column(
        ForeignKey("patients.patient_id"), nullable=True
    )
    room_number: Mapped[str] = mapped_column(String, nullable=False)
    start_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    end_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    is_free: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
