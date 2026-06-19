from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.queries.table_setup import setup_tables
from app.router import user_route, notes, labels
from app.config.logger import get_logger

logger = get_logger("main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_tables()
    logger.info("Fundoo Notes API started")
    yield
    logger.info("Fundoo Notes API stopped")


app = FastAPI(title="Fundoo Notes", version="1.0.0", lifespan=lifespan)

app.include_router(user_route.router)
app.include_router(notes.router)
app.include_router(labels.router)


@app.get("/")
def root():
    return {"message": "Fundoo Notes API is running"}
