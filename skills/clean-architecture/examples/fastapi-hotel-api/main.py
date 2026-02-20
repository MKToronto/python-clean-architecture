from fastapi import FastAPI

from db.database import Base, engine
from routers import bookings, rooms

app = FastAPI(title="Hotel API")


@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)


app.include_router(rooms.router)
app.include_router(bookings.router)
