from fastapi import Depends, FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError

from gws_core.core.exception.exception_handler import ExceptionHandler
from gws_core.external_lab.external_lab_auth import ExternalLabAuth
from gws_core.external_lab.external_lab_dto import (
    ExternalLabImportRequestDTO, ExternalLabImportResourceResponseDTO,
    ExternalLabImportScenarioResponseDTO)
from gws_core.external_lab.external_lab_service import ExternalLabService

external_lab_app = FastAPI(docs_url="/docs")

# Catch HTTP Exceptions


@external_lab_app.exception_handler(HTTPException)
async def all_http_exception_handler(request, exc):
    return ExceptionHandler.handle_exception(request, exc)


# Catch RequestValidationError (422 Unprocessable Entity)
@external_lab_app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc: RequestValidationError):
    return ExceptionHandler.handle_request_validation_error(exc)


# Catch all other exceptions
@external_lab_app.exception_handler(Exception)
async def all_exception_handler(request, exc):
    return ExceptionHandler.handle_exception(request, exc)


@external_lab_app.get("/health-check", summary="Health check route")
def health_check() -> bool:
    """
    Simple health check route
    """

    return True


@external_lab_app.post("/import-resource", summary="Import resource from the lab")
def import_resource(import_dto: ExternalLabImportRequestDTO,
                    _=Depends(ExternalLabAuth.check_auth)) -> ExternalLabImportResourceResponseDTO:
    """
    Import resources from the lab
    """
    return ExternalLabService.import_resource(import_dto)


@external_lab_app.post("/import-scenario", summary="Import scenario from the lab")
def import_scenario(import_dto: ExternalLabImportRequestDTO,
                    _=Depends(ExternalLabAuth.check_auth)) -> ExternalLabImportScenarioResponseDTO:
    """
    Import scenario from the lab
    """
    return ExternalLabService.import_scenario(import_dto)
