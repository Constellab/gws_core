

from typing import Dict, List, Type

from gws_core.brick.brick_dto import BrickInfo
from gws_core.brick.brick_helper import BrickHelper
from gws_core.brick.brick_service import BrickService
from gws_core.core.db.db_manager import AbstractDbManager
from gws_core.core.db.migration.brick_migrator import (BrickMigrator,
                                                       MigrationObject)
from gws_core.core.db.version import Version
from gws_core.core.exception.exceptions.bad_request_exception import \
    BadRequestException
from gws_core.core.utils.logger import Logger
from gws_core.core.utils.settings import Settings
from gws_core.lab.system_dto import BrickMigrationLog


class DbMigrationService:
    """Service to register all brick migrations and call them
    """

    # store the different migration object, where key is brick_name
    _brick_migrators: Dict[str, BrickMigrator] = {}

    _migration_objects: List[MigrationObject] = []

    @classmethod
    def migrate(cls, db_manager_type: Type[AbstractDbManager] = None):
        """Migrate all bricks for the specified db_manager

        :param db_manager_type: The AbstractDbManager type to migrate. Defaults to GwsCoreDbManager.
        :type db_manager_type: Type[AbstractDbManager]
        """

        settings: Settings = Settings.get_instance()

        brick_migrators = cls._get_brick_migrators()

        # If migration objetcs already exists, meaning this is not the first start
        if len(settings.get_brick_migrations_logs()) > 0:
            for migrator in brick_migrators.values():
                migrated = migrator.migrate(db_manager_type)

                if migrated:
                    settings.update_brick_migration_log(
                        migrator.brick_name,
                        str(migrator.current_brick_version),
                        db_manager_type.get_unique_name())

        # save all the brick current version as last migration
        bricks = BrickHelper.get_all_bricks()
        for brick in bricks.values():
            settings.update_brick_migration_log(brick.name, brick.version, db_manager_type.get_unique_name())

    @classmethod
    def _get_brick_migrators(cls) -> Dict[str, BrickMigrator]:
        """ Retrieve all brick migrators for the specified db_manager_type

        """
        if cls._brick_migrators:
            return cls._brick_migrators

        brick_migrators: Dict[str, BrickMigrator] = {}

        for migration_obj in cls._migration_objects:
            brick_info: BrickInfo

            try:
                brick_info = BrickHelper.get_brick_info_and_check(migration_obj.brick_migration)
            except:
                Logger.error(
                    f"Can't retrieve brick information for migration class : '{str(migration_obj.brick_migration)}'")
                continue

            brick_name = brick_info.name
            current_brick_version = Version(brick_info.version)
            migration_version = migration_obj.version

            # Check that the migration version is not higher than the brick version
            if migration_version > current_brick_version:
                BrickService.log_brick_message(
                    brick_name=brick_name,
                    message=f"Error while registering migration for brick {brick_name}. The migration version '{str(migration_version)}' is higher than the brick version '{str(current_brick_version)}'. Skipping migration.",
                    status="ERROR")
                continue

            if brick_name not in brick_migrators:
                # Retrieve previous brick version
                previous_brick_model: BrickMigrationLog = Settings.get_instance().get_brick_migration_log(
                    brick_name)

                if not previous_brick_model:
                    continue

                previous_version = Version(previous_brick_model["version"])
                # create the brick migrator by taking the last brick version
                brick_migrators[brick_name] = BrickMigrator(brick_name, previous_version)

            brick_migrator: BrickMigrator = brick_migrators[brick_name]

            # Check that the migration version was not already registered
            if brick_migrator.has_migration_version(migration_version, migration_obj.get_db_unique_name()):
                BrickService.log_brick_message(
                    brick_name=brick_name,
                    message=f"Error while registering migration for brick {brick_name}. The migration version '{str(migration_version)}' was already registered. Skipping migration.",
                    status="ERROR")
                continue

            brick_migrator.append_migration(migration_obj)

        cls._brick_migrators = brick_migrators
        return cls._brick_migrators

    @classmethod
    def register_migration_object(cls, migration_object: MigrationObject) -> None:
        cls._migration_objects.append(migration_object)

    @classmethod
    def call_migration_manually(cls, brick_name: str,
                                version_str: str,
                                db_unique_name: str) -> None:
        version = Version(version_str)

        brick_migrators = cls._get_brick_migrators()
        brick_migrator = brick_migrators.get(brick_name)
        if brick_migrator is None:
            raise BadRequestException(f"The brick '{brick_name}' does not have migration objects registered")

        brick_migrator.call_migration_manually(version, db_unique_name)

    @classmethod
    def get_brick_migration_versions(cls, brick_name: str) -> List[MigrationObject]:
        brick_migrators = cls._get_brick_migrators()
        if brick_name not in brick_migrators:
            return []

        return brick_migrators[brick_name].get_migration_objects()
