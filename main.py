from fastapi import FastAPI

from appointment_booking.admin import setup_admin
from appointment_booking.database import engine
from appointment_booking.routers.bookings import router as bookings_router
from appointment_booking.routers.doctors import router as doctors_router

app = FastAPI()
app.include_router(doctors_router)
app.include_router(bookings_router)
setup_admin(app, engine)


@app.get("/ping")
def ping():
    return {"status": "ok"}
