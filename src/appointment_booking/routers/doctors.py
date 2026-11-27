from datetime import date, datetime, time, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from appointment_booking.database import get_session
from appointment_booking.models import Doctor, Slot, SlotStatus
from appointment_booking.schemas import DoctorCreate, DoctorRead, SlotRead

router = APIRouter(prefix="/doctors", tags=["doctors"])


@router.post("", response_model=DoctorRead, status_code=status.HTTP_201_CREATED)
async def create_doctor(
    doctor_data: DoctorCreate,
    session: AsyncSession = Depends(get_session),
) -> Doctor:
    doctor = Doctor(**doctor_data.model_dump())
    session.add(doctor)
    await session.commit()
    await session.refresh(doctor)
    return doctor


@router.get("", response_model=list[DoctorRead])
async def get_doctors(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_session),
) -> list[Doctor]:
    stmt = select(Doctor).order_by(Doctor.doctor_id).offset(offset).limit(limit)
    result = await session.execute(stmt)
    return list(result.scalars().all())


@router.get("/{doctor_id}/slots", response_model=list[SlotRead])
async def get_doctor_slots(
    doctor_id: int,
    date_from: date | None = None,
    date_to: date | None = None,
    only_free: bool = True,
    session: AsyncSession = Depends(get_session),
) -> list[Slot]:
    if date_from is not None and date_to is not None and date_from > date_to:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="date_from cannot be greater than date_to",
        )

    doctor = await session.get(Doctor, doctor_id)
    if doctor is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Doctor not found",
        )

    stmt = select(Slot).where(Slot.doctor_id == doctor_id)

    if only_free:
        stmt = stmt.where(
            Slot.status == SlotStatus.FREE,
            Slot.start_time >= datetime.now(),
        )

    if date_from is not None:
        stmt = stmt.where(Slot.start_time >= datetime.combine(date_from, time.min))

    if date_to is not None:
        next_day = date_to + timedelta(days=1)
        stmt = stmt.where(Slot.start_time < datetime.combine(next_day, time.min))

    stmt = stmt.order_by(Slot.start_time.asc())
    result = await session.execute(stmt)
    return list(result.scalars().all())

