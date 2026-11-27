from datetime import datetime
import enum

from sqlalchemy import DateTime, Enum, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from appointment_booking.database import Base


class GenderType(str, enum.Enum):
    male = "male"
    female = "female"


class SlotStatus(str, enum.Enum):
    FREE = "free"
    BOOKED = "booked"
    UNAVAILABLE = "unavailable"


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

    slots: Mapped[list["Slot"]] = relationship(back_populates="patient")

    def __str__(self) -> str:
        return f"{self.name} ({self.telephone})"


class Doctor(Base):
    __tablename__ = "doctors"

    doctor_id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    specialty: Mapped[str] = mapped_column(String, nullable=False)

    doctor_services: Mapped[list["DoctorService"]] = relationship(
        back_populates="doctor"
    )
    slots: Mapped[list["Slot"]] = relationship(back_populates="doctor")

    def __str__(self) -> str:
        return f"{self.name} ({self.specialty})"


class Service(Base):
    __tablename__ = "services"

    service_id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    duration_minutes: Mapped[int] = mapped_column(nullable=False)
    price: Mapped[int] = mapped_column(nullable=False)

    doctor_services: Mapped[list["DoctorService"]] = relationship(
        back_populates="service"
    )
    slots: Mapped[list["Slot"]] = relationship(back_populates="service")

    def __str__(self) -> str:
        return f"{self.name} ({self.price})"


class DoctorService(Base):
    __tablename__ = "doctor_services"
    __table_args__ = (
        UniqueConstraint("doctor_id", "service_id", name="uq_doctor_service"),
    )

    doctor_service_id: Mapped[int] = mapped_column(primary_key=True)
    doctor_id: Mapped[int] = mapped_column(
        ForeignKey("doctors.doctor_id"), nullable=False
    )
    service_id: Mapped[int] = mapped_column(
        ForeignKey("services.service_id"), nullable=False
    )

    doctor: Mapped["Doctor"] = relationship(back_populates="doctor_services")
    service: Mapped["Service"] = relationship(back_populates="doctor_services")

    def __str__(self) -> str:
        return f"Doctor #{self.doctor_id} - Service #{self.service_id}"


class Slot(Base):
    __tablename__ = "slots"
    __table_args__ = (
        UniqueConstraint("doctor_id", "start_time", name="uq_doctor_slot_time"),
    )

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
    status: Mapped[SlotStatus] = mapped_column(
        Enum(SlotStatus, name="slot_status_enum"),
        default=SlotStatus.FREE,
        server_default=SlotStatus.FREE.name,
        nullable=False,
    )

    doctor: Mapped["Doctor"] = relationship(back_populates="slots")
    service: Mapped["Service | None"] = relationship(back_populates="slots")
    patient: Mapped["Patient | None"] = relationship(back_populates="slots")

    def __str__(self) -> str:
        status_label = self.status.value if self.status else SlotStatus.FREE.value
        if self.start_time:
            return f"Slot #{self.slot_id} ({self.start_time:%Y-%m-%d %H:%M}, {status_label})"
        return f"Slot #{self.slot_id} ({status_label})"

