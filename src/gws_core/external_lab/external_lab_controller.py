from fastapi import Depends

from gws_core.core.utils.settings import Settings
from gws_core.external_lab.external_lab_auth import ExternalLabAuth
from gws_core.external_lab.external_lab_dto import (
    ExternalLabImportRequestDTO,
    ExternalLabImportResourceResponseDTO,
    ExternalLabImportScenarioResponseDTO,
)
from gws_core.external_lab.external_lab_service import ExternalLabService
from gws_core.lab.api_registry import ApiRegistry

external_lab_app = ApiRegistry.register_api(
    f"/{Settings.external_lab_api_route_path()}/",
    docs_url="/docs",
    with_exception_handlers=True,
)


@external_lab_app.get("/health-check", summary="Health check route")
def health_check() -> bool:
    """
    Simple health check route
    """

    return True


@external_lab_app.post("/resource/import", summary="Import resource from the lab")
def import_resource(
    import_dto: ExternalLabImportRequestDTO, _=Depends(ExternalLabAuth.check_auth)
) -> ExternalLabImportScenarioResponseDTO:
    """
    Import resources from the lab
    """
    return ExternalLabService.import_resource(import_dto)


@external_lab_app.get(
    "/resource/from-scenario/{scenario_id}",
    summary="Get the imported resource from the import scenario",
)
def get_imported_resource(
    scenario_id: str, _=Depends(ExternalLabAuth.check_auth)
) -> ExternalLabImportResourceResponseDTO:
    """
    Get the imported resource from the import scenario
    """
    return ExternalLabService.get_imported_resource_from_scenario(scenario_id)


@external_lab_app.get("/scenario/{id_}", summary="Get a scenario information")
def get_scenario(
    id_: str, _=Depends(ExternalLabAuth.check_auth)
) -> ExternalLabImportScenarioResponseDTO:
    """
    Get a scenario information
    """
    return ExternalLabService.get_scenario(id_)


@external_lab_app.post("/scenario/import", summary="Import scenario from the lab")
def import_scenario(
    import_dto: ExternalLabImportRequestDTO, _=Depends(ExternalLabAuth.check_auth)
) -> ExternalLabImportScenarioResponseDTO:
    """
    Import scenario from the lab
    """
    return ExternalLabService.import_scenario(import_dto)
