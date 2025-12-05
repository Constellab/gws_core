
from fastapi import Depends
from fastapi.responses import StreamingResponse

from gws_core.brick.brick_dto import BrickDTO
from gws_core.brick.technical_doc_service import TechnicalDocService
from gws_core.core.db.migration.db_migration_service import DbMigrationService
from gws_core.core.db.migration.migration_dto import MigrationDTO
from gws_core.core.utils.response_helper import ResponseHelper

from ..core_controller import core_app
from ..user.authorization_service import AuthorizationService
from .brick_service import BrickService


@core_app.get("/brick", tags=["Bricks"], summary="Get all brick with status")
def get_bricks_status(
    _=Depends(AuthorizationService.check_user_access_token_or_app),
) -> list[BrickDTO]:
    bricks = BrickService.get_all_brick_models()
    return [brick.to_dto() for brick in bricks]


@core_app.get("/brick/{brick_name}", tags=["Bricks"], summary="Get info of a brick")
def get_brick_info(
    brick_name: str, _=Depends(AuthorizationService.check_user_access_token)
) -> BrickDTO | None:
    brick = BrickService.get_brick_model(brick_name)
    if brick is None:
        return None
    return brick.to_dto()


@core_app.post(
    "/brick/{brick_name}/technical-doc",
    tags=["Bricks"],
    summary="Generate technical doc for a brick",
)
def export_technical_doc(
    brick_name: str, _=Depends(AuthorizationService.check_user_access_token)
) -> StreamingResponse:
    return ResponseHelper.create_file_response_from_object(
        TechnicalDocService.generate_technical_doc(brick_name), brick_name + "_technical_doc.json"
    )


@core_app.post(
    "/brick/{brick_name}/call-migration/{version}/{db_unique_name}",
    tags=["Bricks"],
    summary="Call a specific migration",
)
def call_migration(
    brick_name: str,
    version: str,
    db_unique_name: str,
    _=Depends(AuthorizationService.check_user_access_token),
) -> None:
    DbMigrationService.call_migration_manually(brick_name, version, db_unique_name)


@core_app.get(
    "/brick/{brick_name}/migrations",
    tags=["Bricks"],
    summary="Get the list of migration version available for a brick",
)
def get_brick_migration_versions(
    brick_name: str, _=Depends(AuthorizationService.check_user_access_token)
) -> list[MigrationDTO]:
    migrations = DbMigrationService.get_brick_migration_versions(brick_name)
    return [migration.to_dto() for migration in migrations]
