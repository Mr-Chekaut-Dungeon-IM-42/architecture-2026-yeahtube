from fastapi import FastAPI
from fastapi.responses import JSONResponse
from starlette.requests import Request

from app.domain.errors import DomainError, NotFoundError


async def domain_error_handler(request: Request, exc: Exception) -> JSONResponse:
    # The domain message is already expressed in business language.
    return JSONResponse(status_code=409, content={"detail": str(exc)})


async def not_found_error_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(status_code=404, content={"detail": str(exc)})


def register_exception_handlers(app: FastAPI) -> None:
    # Order matters: the more specific handler should be registered explicitly.
    app.add_exception_handler(NotFoundError, not_found_error_handler)
    app.add_exception_handler(DomainError, domain_error_handler)
