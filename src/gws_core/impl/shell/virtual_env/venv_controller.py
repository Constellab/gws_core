from fastapi import Depends

from gws_core.core.model.model_dto import BaseModelDTO
from gws_core.impl.shell.virtual_env.venv_dto import VEnsStatusDTO, VEnvCompleteInfoDTO
from gws_core.impl.shell.virtual_env.venv_service import VEnvService
from gws_core.user.authorization_service import AuthorizationService

from ....core_controller import core_app


@core_app.get("/venv", tags=["VEnv"], summary="Get the list of virtual environments")
def get_venv_list(_=Depends(AuthorizationService.check_user_access_token)) -> VEnsStatusDTO:
    """Retrieve the list of all virtual environments.

    Returns status information for all virtual environments managed by the system,
    including their names, creation info, and locations.

    :return: Status DTO containing the list of virtual environments
    :rtype: VEnsStatusDTO
    """

    return VEnvService.get_vens_status()


class VenvNameRequest(BaseModelDTO):
    """Request body for virtual environment operations that require a venv name."""
    venv_name: str


@core_app.post("/venv/get", tags=["VEnv"], summary="Get a virtual environment")
def get_venv(
    venv_name: VenvNameRequest, _=Depends(AuthorizationService.check_user_access_token)
) -> VEnvCompleteInfoDTO:
    """Get complete information about a specific virtual environment.

    Uses POST with a body to pass the venv name because the name may contain
    special characters that are problematic in URL paths.

    :param venv_name: Request containing the virtual environment name
    :type venv_name: VenvNameRequest
    :return: Complete information about the virtual environment
    :rtype: VEnvCompleteInfoDTO
    """

    return VEnvService.get_venv_complete_info(venv_name.venv_name)


@core_app.post("/venv/delete", tags=["VEnv"], summary="Delete a virtual environment")
def delete_venv(
    venv_name: VenvNameRequest, _=Depends(AuthorizationService.check_user_access_token)
) -> None:
    """Delete a specific virtual environment.

    Uses POST with a body to pass the venv name because the name may contain
    special characters. Checks for running scenarios before deletion to prevent
    conflicts.

    :param venv_name: Request containing the virtual environment name to delete
    :type venv_name: VenvNameRequest
    :raises BadRequestException: If a scenario is currently running
    """
    VEnvService.delete_venv(venv_name.venv_name, check_running_scenario=True)


@core_app.delete("/venv", tags=["VEnv"], summary="Delete all virtual environments")
def delete_all_venv(_=Depends(AuthorizationService.check_user_access_token)) -> None:
    """Delete all virtual environments.

    Removes all virtual environments managed by the system. Checks for running
    scenarios before deletion to prevent conflicts.

    :raises BadRequestException: If any scenario is currently running
    """
    VEnvService.delete_all_venvs()
