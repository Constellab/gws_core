
from fastapi import Depends

from gws_core.core.model.model_dto import BaseModelDTO
from gws_core.impl.shell.virtual_env.venv_dto import (VEnsStatusDTO,
                                                      VEnvCompleteInfoDTO)
from gws_core.impl.shell.virtual_env.venv_service import VEnvService
from gws_core.user.authorization_service import AuthorizationService

from ....core_controller import core_app


@core_app.get("/venv", tags=["VEnv"],
              summary="Get the list of virtual environments")
def get_venv_list(_=Depends(AuthorizationService.check_user_access_token)) -> VEnsStatusDTO:
    """
    Retrieve a list of running scenarios.
    """

    return VEnvService.get_vens_status()


class VenvNameRequest(BaseModelDTO):
    venv_name: str


@core_app.post("/venv/get", tags=["VEnv"],
               summary="Get a virtual environment")
def get_venv(venv_name: VenvNameRequest,
             _=Depends(AuthorizationService.check_user_access_token)) -> VEnvCompleteInfoDTO:
    """
    Use a post and body to retrieve the name because the name can be weird
    """

    return VEnvService.get_venv_complete_info(venv_name.venv_name)


@core_app.post("/venv/delete", tags=["VEnv"],
               summary="Delete a virtual environment")
def delete_venv(venv_name: VenvNameRequest,
                _=Depends(AuthorizationService.check_user_access_token)) -> None:
    """
    Delete a virtual environment
    Use body to retrieve the name because the name can be weird
    """
    VEnvService.delete_venv(venv_name.venv_name, check_running_scenario=True)


@core_app.delete("/venv", tags=["VEnv"],
                 summary="Delete all virtual environments")
def delete_all_venv(
        _=Depends(AuthorizationService.check_user_access_token)) -> None:
    """
    Delete all virtual environments
    """
    VEnvService.delete_all_venvs()
