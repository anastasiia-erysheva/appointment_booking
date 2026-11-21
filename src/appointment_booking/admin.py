import secrets
from typing import Any

from fastapi import FastAPI
from sqladmin import Admin, ModelView
from sqladmin.authentication import AuthenticationBackend
from sqlalchemy.ext.asyncio import AsyncEngine
from starlette.requests import Request
from wtforms import ValidationError

from appointment_booking.config import settings
from appointment_booking.models import Doctor, DoctorService, Patient, Service, Slot


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
        Slot.is_free,
    ]
    column_searchable_list = [Slot.room_number]
    column_sortable_list = [
        Slot.slot_id,
        Slot.room_number,
        Slot.start_time,
        Slot.end_time,
        Slot.is_free,
    ]
    name = "Slot"
    name_plural = "Slots"
    icon = "fa-solid fa-calendar-check"

    async def on_model_change(
        self, data: dict[str, Any], model: Slot, is_created: bool, request: Request
    ) -> None:
        start_time = data.get("start_time") or model.start_time
        end_time = data.get("end_time") or model.end_time
        if start_time and end_time and end_time <= start_time:
            raise ValidationError("End time must be after start time.")

        has_patient = bool(data.get("patient"))
        if has_patient:
            data["is_free"] = False
            model.is_free = False
        else:
            data["is_free"] = True
            data["service"] = None
            model.is_free = True
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
