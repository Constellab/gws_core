# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from typing import List, Optional

from fastapi import Depends

from gws_core.brick.brick_dto import BrickDTO
from gws_core.brick.technical_doc_service import TechnicalDocService
from gws_core.core.db.db_migration import DbMigrationService
from gws_core.core.db.migration_dto import MigrationDTO

from ..core_controller import core_app
from ..user.auth_service import AuthService
from .brick_service import BrickService


@core_app.get("/brick", tags=["Bricks"], summary="Get all brick with status")
def get_bricks_status(_=Depends(AuthService.check_user_access_token)) -> List[BrickDTO]:
    bricks = BrickService.get_all_brick_models()
    return [brick.to_dto() for brick in bricks]


@core_app.get("/brick/{brick_name}", tags=["Bricks"], summary="Get info of a brick")
def get_brick_info(brick_name: str, _=Depends(AuthService.check_user_access_token)) -> Optional[BrickDTO]:
    brick = BrickService.get_brick_model(brick_name)
    if brick is None:
        return None
    return brick.to_dto()

# TODO TO TEST AND TYPE


@core_app.get("/brick/{brick_name}/technical-doc", tags=["Bricks"], summary="Generate technical doc for a brick")
def export_technical_doc(brick_name: str,
                         _=Depends(AuthService.check_user_access_token)) -> dict:
    res = TechnicalDocService.generate_technical_doc(brick_name)
    return res


@core_app.post("/brick/{brick_name}/call-migration/{version}",  tags=["Bricks"], summary="Call a specific migration")
def call_migration(brick_name: str,
                   version: str,
                   _=Depends(AuthService.check_user_access_token)) -> None:
    DbMigrationService.call_migration_manually(brick_name, version)


@core_app.get("/brick/{brick_name}/migrations", tags=["Bricks"],
              summary="Get the list of migration version available for a brick")
def get_brick_migration_versions(brick_name: str,
                                 _=Depends(AuthService.check_user_access_token)) -> List[MigrationDTO]:
    migrations = DbMigrationService.get_brick_migration_versions(brick_name)
    return [migration.to_dto() for migration in migrations]
