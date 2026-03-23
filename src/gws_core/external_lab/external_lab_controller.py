from fastapi import Depends
from fastapi.responses import FileResponse

from gws_core.core.utils.settings import Settings
from gws_core.external_lab.external_lab_auth import ExternalLabAuth
from gws_core.external_lab.external_lab_dto import (
    ExternalLabImportRequestDTO,
    ExternalLabImportResourceResponseDTO,
    ExternalLabImportScenarioResponseDTO,
    MarkEntityAsSharedDTO,
)
from gws_core.external_lab.external_lab_service import ExternalLabService
from gws_core.lab.api_registry import ApiRegistry
from gws_core.lab.lab_model.lab_dto import LabDTO
from gws_core.share.shared_dto import (
    ShareLinkEntityType,
    ShareResourceZippedResponseDTO,
    ShareScenarioInfoReponseDTO,
)
from gws_core.user.user_dto import UserDTO

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


@external_lab_app.post("/scenario/trigger-download", summary="Trigger download of an external scenario")
def trigger_scenario_download(
    import_dto: ExternalLabImportRequestDTO, _=Depends(ExternalLabAuth.check_auth)
) -> ExternalLabImportScenarioResponseDTO:
    """
    Called by an external lab (Lab A) to trigger this lab (Lab B) to download
    a scenario from Lab A. Lab B will then make requests back to Lab A to
    fetch the scenario data.
    """
    return ExternalLabService.trigger_scenario_download(import_dto)


@external_lab_app.get("/lab-info", summary="Get current lab information")
def get_current_lab_info(
    _=Depends(ExternalLabAuth.check_auth),
) -> LabDTO:
    """
    Get information about the current lab (name, space, etc.)
    """
    return ExternalLabService.get_current_lab_info()


@external_lab_app.get("/user/{user_id}", summary="Get user information")
def get_user_info(user_id: str, _=Depends(ExternalLabAuth.check_auth)) -> UserDTO:
    """
    Get user information by id. If the user doesn't exist locally,
    imports them from Constellab as inactive.
    """
    return ExternalLabService.get_user_info(user_id)


@external_lab_app.put("/scenario/{id_}/stop", summary="Stop a running scenario")
def stop_scenario(
    id_: str, _=Depends(ExternalLabAuth.check_auth)
) -> ExternalLabImportScenarioResponseDTO:
    """
    Stop a running scenario
    """
    return ExternalLabService.stop_scenario(id_)


@external_lab_app.get(
    "/scenario/{id_}/export-info",
    summary="Get scenario export info for downloading",
)
def get_scenario_export_info(
    id_: str, _=Depends(ExternalLabAuth.check_auth)
) -> ShareScenarioInfoReponseDTO:
    """
    Get scenario export info for credential-based downloading.
    Returns the scenario export package and resource routes.
    """
    return ExternalLabService.get_scenario_export_info(id_)


@external_lab_app.post(
    "/resource/{resource_id}/zip",
    summary="Zip a resource for download",
)
def zip_resource(
    resource_id: str, _=Depends(ExternalLabAuth.check_auth)
) -> ShareResourceZippedResponseDTO:
    """
    Zip a resource for credential-based download.
    """
    return ExternalLabService.zip_resource(resource_id)


@external_lab_app.get(
    "/resource/{resource_id}/download",
    summary="Download a zipped resource",
)
def download_resource(
    resource_id: str, _=Depends(ExternalLabAuth.check_auth)
) -> FileResponse:
    """
    Download a zipped resource using credentials.
    """
    return ExternalLabService.download_resource(resource_id)


@external_lab_app.post(
    "/{entity_type}/mark-as-shared/{entity_id}",
    summary="Mark an entity as downloaded by another lab",
)
def mark_entity_as_shared(
    entity_type: ShareLinkEntityType,
    entity_id: str,
    body: MarkEntityAsSharedDTO,
    _=Depends(ExternalLabAuth.check_auth),
) -> None:
    """
    Called by an external lab after it has successfully imported an entity
    via credential-based sharing. This marks the entity as sent to the
    requesting lab.
    """
    ExternalLabService.mark_entity_as_shared(entity_type, entity_id, body)
