

from typing import Callable, Type

from gws_core.brick.brick_service import BrickService
from gws_core.core.db.db_manager import AbstractDbManager
from gws_core.core.db.gws_core_db_manager import GwsCoreDbManager
from gws_core.core.db.migration.brick_migrator import (BrickMigration,
                                                       MigrationObject)
from gws_core.core.db.migration.db_migration_service import DbMigrationService
from gws_core.core.db.version import Version
from gws_core.core.utils.utils import Utils


def brick_migration(
        version: str,
        short_description: str,
        authenticate_sys_user: bool = True,
        db_manager_type: Type[AbstractDbManager] = None) -> Callable:
    """Decorator to place on sub class of BrickMigration to declare a new migration code

    :param version: version of this migration
    :type version: str
    :param short_description: short description of the migration
    :type short_description: str
    :param authenticate_sys_user: if True, the migration will be executed with the sys user authenticated.
                                  Can be useful to set to False when User table is changed.
    :type authenticate_sys_user: bool
    :param db_manager_type: The DbManager type to use for the migration. Defaults to GwsCoreDbManager.
    :type db_manager_type: Type
    :return: [description]
    :rtype: Callable
    """

    def decorator(class_: Type[BrickMigration]):

        if not Utils.issubclass(class_, BrickMigration):
            BrickService.log_brick_error(
                class_,
                f"The brick_migration decorator is used on class '{class_.__name__}' but this class is not a subclass of BrickMigration")
            return class_

        try:
            version_obj = Version(version)
        except:
            BrickService.log_brick_error(
                class_,
                f"The version '{version}' used in brick_migration decorator on class '{class_.__name__}' is invalid")
            return class_

        # Register the migration
        DbMigrationService.register_migration_object(MigrationObject(
            class_, version_obj, short_description, authenticate_sys_user, db_manager_type or GwsCoreDbManager))

        return class_

    return decorator
