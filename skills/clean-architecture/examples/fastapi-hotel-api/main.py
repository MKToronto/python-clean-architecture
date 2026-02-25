from contextlib import asynccontextmanager

from fastapi import FastAPI

from db.database import Base, engine
from routers import bookings, rooms


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="Hotel API", lifespan=lifespan)

app.include_router(rooms.router)
app.include_router(bookings.router)
