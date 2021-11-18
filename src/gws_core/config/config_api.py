# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from fastapi import Depends

from ..config.config_types import ConfigParamsDict
from ..core_app import core_app
from ..user.auth_service import AuthService
from ..user.user_dto import UserData
from .config_service import ConfigService


@core_app.put("/config/{id}", tags=["Config"], summary="Update the config values")
def get_the_experiment_queue(id: str,
                             config_params: ConfigParamsDict,
                             _: UserData = Depends(AuthService.check_user_access_token)) -> dict:
    """
    Update the configuration params
    """

    return ConfigService.update_config_params_with_id(id, config_params).to_json(deep=True)
