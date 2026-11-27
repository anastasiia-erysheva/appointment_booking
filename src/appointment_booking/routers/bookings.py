from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from appointment_booking.database import get_session
from appointment_booking.models import (
    DoctorService,
    Patient,
    Service,
    Slot,
    SlotStatus,
)
from appointment_booking.schemas import BookingCreate, BookingRead

router = APIRouter(prefix="/bookings", tags=["bookings"])


@router.post("", response_model=BookingRead, status_code=status.HTTP_201_CREATED)
async def create_booking(
    payload: BookingCreate,
    session: AsyncSession = Depends(get_session),
) -> Slot:
    """Book an available slot for a patient."""
    slot_stmt = (
        select(Slot)
        .where(Slot.slot_id == payload.slot_id)
        .with_for_update()
    )
    slot_result = await session.execute(slot_stmt)
    slot = slot_result.scalar_one_or_none()

    if slot is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Slot not found",
        )

    if slot.status != SlotStatus.FREE or slot.patient_id is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Slot is not available for booking",
        )

    if slot.start_time < datetime.now():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot book a slot in the past",
        )

    service_stmt = select(Service).where(Service.service_id == payload.service_id)
    service_result = await session.execute(service_stmt)
    if service_result.scalar_one_or_none() is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service not found",
        )

    doctor_service_stmt = select(DoctorService).where(
        DoctorService.doctor_id == slot.doctor_id,
        DoctorService.service_id == payload.service_id,
    )
    doctor_service_result = await session.execute(doctor_service_stmt)
    if doctor_service_result.scalar_one_or_none() is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Doctor does not provide the selected service",
        )

    patient_stmt = select(Patient).where(Patient.telephone == payload.telephone)
    patient_result = await session.execute(patient_stmt)
    patient = patient_result.scalar_one_or_none()

    if patient is None:
        if payload.email is not None:
            email_check = await session.execute(
                select(Patient).where(Patient.email == payload.email)
            )
            if email_check.scalar_one_or_none() is not None:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Patient with this email already exists",
                )

        if payload.telegram_id is not None:
            tg_check = await session.execute(
                select(Patient).where(Patient.telegram_id == payload.telegram_id)
            )
            if tg_check.scalar_one_or_none() is not None:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Patient with this telegram_id already exists",
                )

        patient = Patient(
            name=payload.patient_name,
            telephone=payload.telephone,
            email=payload.email,
            telegram_id=payload.telegram_id,
        )
        session.add(patient)
        try:
            await session.flush()
        except IntegrityError as exc:
            await session.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Patient contact data conflicts with an existing record",
            ) from exc

    slot.patient_id = patient.patient_id
    slot.service_id = payload.service_id
    slot.status = SlotStatus.BOOKED

    await session.commit()
    await session.refresh(slot)
    return slot
