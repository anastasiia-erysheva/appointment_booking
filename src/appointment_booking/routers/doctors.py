from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from appointment_booking.database import get_session
from appointment_booking.models import Doctor
from appointment_booking.schemas import DoctorCreate, DoctorRead

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
