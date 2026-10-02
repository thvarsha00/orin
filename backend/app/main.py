import logging

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from app.api import auth, coding, documents, health, tutor
from app.config import settings
from app.database import init_db
from app.services.ai import AIError
from app.services.rag.ingestion import recover_interrupted

logger = logging.getLogger("orin")
app = FastAPI(title="Orin API", version="0.1.0")

app.add_middleware(CORSMiddleware, allow_origins=[o.strip() for o in settings.cors_origins.split(",")],
                   allow_credentials=True, allow_methods=["*"], allow_headers=["*"],
                   expose_headers=["X-Conversation-Id"])

for r in (health.router, auth.router, tutor.router, documents.router, coding.router):
    app.include_router(r)


@app.on_event("startup")
def startup() -> None:
    init_db()
    recover_interrupted()


def _err(status: int, msg: str) -> JSONResponse:
    return JSONResponse(status_code=status, content={"error": msg})


@app.exception_handler(HTTPException)
async def http_exc(_: Request, exc: HTTPException):
    return _err(exc.status_code, str(exc.detail))


@app.exception_handler(AIError)
async def ai_exc(_: Request, exc: AIError):
    return _err(exc.status_code, exc.message)


@app.exception_handler(RequestValidationError)
async def validation_exc(_: Request, exc: RequestValidationError):
    first = exc.errors()[0]
    field = ".".join(str(p) for p in first["loc"][1:]) or "input"
    return _err(422, f"Invalid {field}: {first['msg']}")


@app.exception_handler(SQLAlchemyError)
async def db_exc(_: Request, exc: SQLAlchemyError):
    logger.exception("Database error")
    return _err(500, "A database error occurred. Please try again.")


@app.exception_handler(Exception)
async def unhandled(_: Request, exc: Exception):
    logger.exception("Unhandled error")
    return _err(500, "Something went wrong on our side. Please try again.")
