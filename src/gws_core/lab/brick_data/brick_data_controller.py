
from typing import List

from fastapi.param_functions import Depends
from pydantic import BaseModel

from gws_core.lab.brick_data.brick_data_dto import BrickDataDTO

from ...core_controller import core_app
from ...user.auth_service import AuthService
from .brick_data_service import BrickDataService


@core_app.get("/brick-data", tags=["Brick data"], summary="Get brick data info")
def get_brick_data_list(_=Depends(AuthService.check_user_access_token)) -> List[BrickDataDTO]:
    """
    Reset dev environment
    """

    return BrickDataService.get_brick_data_list()


class DeleteBrickData(BaseModel):
    fs_node_path: str


@core_app.post("/brick-data/delete", tags=["Brick data"], summary="Delete a brick data")
def delete_brick_data(delete_brick_data: DeleteBrickData,
                      _=Depends(AuthService.check_user_access_token)) -> None:
    """
    Reset dev environment
    """

    BrickDataService.delete_brick_data(delete_brick_data.fs_node_path)


@core_app.delete("/brick-data", tags=["Brick data"], summary="Delete all brick data")
def delete_all_brick_data(_=Depends(AuthService.check_user_access_token)) -> None:
    """
    Reset dev environment
    """

    BrickDataService.delete_all_brick_data()
