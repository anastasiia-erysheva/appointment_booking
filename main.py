from fastapi import FastAPI

from appointment_booking.routers.doctors import router as doctors_router

app = FastAPI()
app.include_router(doctors_router)


@app.get("/ping")
def ping():
    return {"status": "ok"}
