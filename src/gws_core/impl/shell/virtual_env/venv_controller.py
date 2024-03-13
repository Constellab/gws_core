
from fastapi import Depends
from pydantic import BaseModel

from gws_core.impl.shell.virtual_env.venv_dto import (VEnsStatusDTO,
                                                      VEnvCompleteInfoDTO)
from gws_core.impl.shell.virtual_env.venv_service import VEnvService
from gws_core.user.auth_service import AuthService

from ....core_controller import core_app


@core_app.get("/venv", tags=["VEnv"],
              summary="Get the list of virtual environments")
def get_venv_list(_=Depends(AuthService.check_user_access_token)) -> VEnsStatusDTO:
    """
    Retrieve a list of running experiments.
    """

    return VEnvService.get_vens_status()


class VenvNameRequest(BaseModel):
    venv_name: str


@core_app.post("/venv/get", tags=["VEnv"],
               summary="Get a virtual environment")
def get_venv(venv_name: VenvNameRequest,
             _=Depends(AuthService.check_user_access_token)) -> VEnvCompleteInfoDTO:
    """
    Use a post and body to retrieve the name because the name can be weird
    """

    return VEnvService.get_venv_complete_info(venv_name.venv_name)


@core_app.post("/venv/delete", tags=["VEnv"],
               summary="Delete a virtual environment")
def delete_venv(venv_name: VenvNameRequest,
                _=Depends(AuthService.check_user_access_token)) -> None:
    """
    Delete a virtual environment
    Use body to retrieve the name because the name can be weird
    """
    VEnvService.delete_venv(venv_name.venv_name, check_running_experiment=True)


@core_app.delete("/venv", tags=["VEnv"],
                 summary="Delete all virtual environments")
def delete_all_venv(
        _=Depends(AuthService.check_user_access_token)) -> None:
    """
    Delete all virtual environments
    """
    VEnvService.delete_all_venvs()
