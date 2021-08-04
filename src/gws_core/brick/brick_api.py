# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import importlib
from typing import Optional

from fastapi import Depends
from fastapi.responses import JSONResponse

from ..core.exception.exceptions import BadRequestException
from ..core_app import core_app
from ..user.auth_service import AuthService
from ..user.user_dto import UserData


@core_app.post("/brick/{brick_name}/{api_func}", response_class=JSONResponse, tags=["Bricks APIs"], summary="Call custom brick APIs")
async def call_a_custom_brick_api(brick_name: Optional[str] = "gws",
                                  api_func: Optional[str] = None,
                                  data: Optional[dict] = None,
                                  _: UserData = Depends(AuthService.check_user_access_token)) -> dict:
    """
    Call a custom api function of a brick

    - **brick_name**: the name of the brick
    - **api_func**: the target api function.
    - **data**: custom json data
    For example of **brick_name=foo** and **api_func=do-thing**, the method **foo.app.API.do_thing( data )** with be called if it exists. Function **do_thing** must return a JSON response as a dictionnary.
    """

    try:
        brick_app_module = importlib.import_module(f"{brick_name}.app")
        api_t = getattr(brick_app_module, "API", None)
        if api_t is None:
            raise BadRequestException(f"Class {brick_name}.app.API not found")

        api_func = api_func.replace("-", "_").lower()
        async_func = getattr(api_t, api_func, None)
        if async_func is None:
            raise BadRequestException(
                f"Method {brick_name}.app.API.{api_func} not found")
        else:
            return await async_func(data)
    except Exception as err:
        raise BadRequestException(
            f"Cannot call custom brick api. Error {err}.") from err
