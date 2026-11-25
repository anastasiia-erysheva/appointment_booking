import secrets
from typing import Any

from fastapi import FastAPI
from sqladmin import Admin, ModelView
from sqladmin.authentication import AuthenticationBackend
from sqlalchemy.ext.asyncio import AsyncEngine
from starlette.requests import Request
from wtforms import ValidationError

from appointment_booking.config import settings
from appointment_booking.models import (
    Doctor,
    DoctorService,
    Patient,
    Service,
    Slot,
    SlotStatus,
)


class AdminAuth(AuthenticationBackend):
    async def login(self, request: Request) -> bool:
        form = await request.form()
        username = str(form.get("username", ""))
        password = str(form.get("password", ""))

        is_valid_user = secrets.compare_digest(username, settings.ADMIN_USERNAME)
        is_valid_pass = secrets.compare_digest(password, settings.ADMIN_PASSWORD)

        if is_valid_user and is_valid_pass:
            request.session.update({"authenticated": True})
            return True
        return False

    async def logout(self, request: Request) -> bool:
        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> bool:
        return bool(request.session.get("authenticated", False))


class PatientAdmin(ModelView, model=Patient):
    column_list = [
        Patient.patient_id,
        Patient.name,
        Patient.gender,
        Patient.telephone,
        Patient.email,
        Patient.telegram_id,
    ]
    column_searchable_list = [Patient.name, Patient.telephone, Patient.email]
    column_sortable_list = [Patient.patient_id, Patient.name]
    form_excluded_columns = [Patient.slots]
    can_delete = False
    name = "Patient"
    name_plural = "Patients"
    icon = "fa-solid fa-hospital-user"

    async def on_model_change(
        self, data: dict[str, Any], model: Patient, is_created: bool, request: Request
    ) -> None:
        for field in ("email", "telegram_id"):
            value = data.get(field)
            if isinstance(value, str) and not value.strip():
                data[field] = None
                setattr(model, field, None)


class DoctorAdmin(ModelView, model=Doctor):
    column_list = [
        Doctor.doctor_id,
        Doctor.name,
        Doctor.specialty,
    ]
    column_searchable_list = [Doctor.name, Doctor.specialty]
    column_sortable_list = [Doctor.doctor_id, Doctor.name, Doctor.specialty]
    form_excluded_columns = [Doctor.doctor_services, Doctor.slots]
    can_delete = False
    name = "Doctor"
    name_plural = "Doctors"
    icon = "fa-solid fa-user-doctor"


class ServiceAdmin(ModelView, model=Service):
    column_list = [
        Service.service_id,
        Service.name,
        Service.duration_minutes,
        Service.price,
    ]
    column_searchable_list = [Service.name]
    column_sortable_list = [
        Service.service_id,
        Service.name,
        Service.duration_minutes,
        Service.price,
    ]
    form_excluded_columns = [Service.doctor_services, Service.slots]
    can_delete = False
    name = "Service"
    name_plural = "Services"
    icon = "fa-solid fa-stethoscope"

    async def on_model_change(
        self, data: dict[str, Any], model: Service, is_created: bool, request: Request
    ) -> None:
        price = data.get("price") if data.get("price") is not None else model.price
        duration = (
            data.get("duration_minutes")
            if data.get("duration_minutes") is not None
            else model.duration_minutes
        )
        if price is not None and price < 0:
            raise ValidationError("Price must be greater than or equal to 0.")
        if duration is not None and duration <= 0:
            raise ValidationError("Duration must be greater than 0 minutes.")


class DoctorServiceAdmin(ModelView, model=DoctorService):
    column_list = [
        DoctorService.doctor_service_id,
        DoctorService.doctor,
        DoctorService.service,
    ]
    column_sortable_list = [DoctorService.doctor_service_id]
    name = "Doctor Service"
    name_plural = "Doctor Services"
    icon = "fa-solid fa-link"


class SlotAdmin(ModelView, model=Slot):
    column_list = [
        Slot.slot_id,
        Slot.doctor,
        Slot.service,
        Slot.patient,
        Slot.room_number,
        Slot.start_time,
        Slot.end_time,
        Slot.status,
    ]
    column_searchable_list = [Slot.room_number]
    column_sortable_list = [
        Slot.slot_id,
        Slot.room_number,
        Slot.start_time,
        Slot.end_time,
        Slot.status,
    ]
    name = "Slot"
    name_plural = "Slots"
    icon = "fa-solid fa-calendar-check"

    @staticmethod
    def _normalize_status(raw_status: Any) -> SlotStatus | None:
        if isinstance(raw_status, SlotStatus):
            return raw_status
        if isinstance(raw_status, str):
            if raw_status in SlotStatus.__members__:
                return SlotStatus[raw_status]
            try:
                return SlotStatus(raw_status.lower())
            except ValueError:
                return None
        return None

    async def on_model_change(
        self, data: dict[str, Any], model: Slot, is_created: bool, request: Request
    ) -> None:
        start_time = data.get("start_time") or model.start_time
        end_time = data.get("end_time") or model.end_time
        if start_time and end_time and end_time <= start_time:
            raise ValidationError("End time must be after start time.")

        patient = data["patient"] if "patient" in data else model.patient
        service = data["service"] if "service" in data else model.service
        raw_status = data["status"] if "status" in data else model.status
        status = self._normalize_status(raw_status) or SlotStatus.FREE

        has_patient = bool(patient)
        has_service = bool(service)

        if has_patient:
            if not has_service:
                raise ValidationError("Service is required when a patient is assigned.")
            if status == SlotStatus.UNAVAILABLE:
                raise ValidationError(
                    "Cannot set status to UNAVAILABLE when a patient is assigned."
                )
            data["status"] = SlotStatus.BOOKED.name
            model.status = SlotStatus.BOOKED
        else:
            if status == SlotStatus.BOOKED:
                prev_has_patient = not is_created and bool(
                    model.patient_id or model.patient
                )
                if prev_has_patient:
                    status = SlotStatus.FREE
                else:
                    raise ValidationError(
                        "Cannot set status to BOOKED without an assigned patient."
                    )
            data["status"] = status.name
            model.status = status
            data["service"] = None
            model.service_id = None


def setup_admin(app: FastAPI, engine: AsyncEngine) -> Admin:
    authentication_backend = AdminAuth(secret_key=settings.ADMIN_SECRET_KEY)
    admin = Admin(app, engine, authentication_backend=authentication_backend)
    admin.add_view(PatientAdmin)
    admin.add_view(DoctorAdmin)
    admin.add_view(ServiceAdmin)
    admin.add_view(DoctorServiceAdmin)
    admin.add_view(SlotAdmin)
    return admin
