

from typing import Callable, Dict, List, Type

from gws_core.brick.brick_helper import BrickHelper
from gws_core.brick.brick_service import BrickService
from gws_core.core.exception.exceptions.bad_request_exception import \
    BadRequestException
from gws_core.core.utils.logger import Logger
from gws_core.core.utils.settings import Settings
from gws_core.core.utils.utils import Utils
from gws_core.lab.system_dto import BrickMigrationLog, ModuleInfo

from .brick_migrator import BrickMigration, BrickMigrator, MigrationObject
from .version import Version


class DbMigrationService:
    """Service to register all brick migrations and call them
    """

    # store the different migration object, where key is brick
    _brick_migrators: Dict[str, BrickMigrator] = {}

    _migration_objects: List[MigrationObject] = []

    @classmethod
    def migrate(cls):
        settings: Settings = Settings.get_instance()

        cls._init_brick_migrators()

        # If migration objetcs already exists, meaning this is not the first start
        if len(settings.get_brick_migrations_logs()) > 0:
            for migrator in cls._brick_migrators.values():
                migrated = migrator.migrate()

                if migrated:
                    settings.update_brick_migration_log(migrator.brick_name, str(migrator.current_brick_version))

        # save all the brick current version as last migration
        bricks = BrickHelper.get_all_bricks()
        for brick in bricks.values():
            settings.update_brick_migration_log(brick["name"], brick["version"])

    @classmethod
    def _init_brick_migrators(cls) -> None:
        """ Init the _brick_migrators object with the migrators

        :return: _description_
        :rtype: _type_
        """
        brick_migrators: Dict[str, BrickMigrator] = {}

        for migration_obj in cls._migration_objects:
            brick_info: ModuleInfo

            try:
                brick_info = BrickHelper.get_brick_info_and_check(migration_obj.brick_migration)
            except:
                Logger.error(
                    f"Can't retrieve brick information for migration class : '{str(migration_obj.brick_migration)}'")
                continue

            brick_name = brick_info["name"]
            current_brick_version = Version(brick_info["version"])
            migration_version = migration_obj.version

            # Check that the migration version is not higher than the brick version
            if migration_version > current_brick_version:
                BrickService.log_brick_message(
                    brick_name=brick_name,
                    message=f"Error while registering migration for brick {brick_name}. The migration version '{str(migration_version)}' is higher than the brick version '{str(current_brick_version)}'. Skipping migration.",
                    status="ERROR")
                continue

            if not brick_name in brick_migrators:
                # Retrieive previous brick version
                previous_brick_model: BrickMigrationLog = Settings.get_instance().get_brick_migration_log(brick_name)

                if not previous_brick_model:
                    Logger.info(f"Skipping migration for brick {brick_name} because it is new")
                    continue

                previous_version = Version(previous_brick_model["version"])
                # create the brick migrator by taking the last brick version
                brick_migrators[brick_name] = BrickMigrator(brick_name, previous_version)

            brick_migrator: BrickMigrator = brick_migrators[brick_name]

            # Check that the migration version was not already registered
            if brick_migrator.has_migration_version(migration_version):
                BrickService.log_brick_message(
                    brick_name=brick_name,
                    message=f"Error while registering migration for brick {brick_name}. The migration version '{str(migration_version)}' was already registered. Skipping migration.",
                    status="ERROR")
                continue

            brick_migrator.append_migration(migration_obj)

        cls._brick_migrators = brick_migrators

    @classmethod
    def register_migration_object(cls, migration_object: MigrationObject) -> None:
        cls._migration_objects.append(migration_object)

    @classmethod
    def call_migration_manually(cls, brick_name: str, version_str: str) -> None:
        version = Version(version_str)

        brick_migrator = cls._brick_migrators.get(brick_name)
        if brick_migrator is None:
            raise BadRequestException(f"The brick '{brick_name}' does not have migration objects registered")

        brick_migrator.call_migration_manually(version)

    @classmethod
    def get_brick_migration_versions(cls, brick_name: str) -> List[MigrationObject]:
        if brick_name not in cls._brick_migrators:
            return []

        return cls._brick_migrators[brick_name].get_migration_objects()


def brick_migration(version: str, short_description: str, authenticate_sys_user: bool = True) -> Callable:
    """Decorator to place on sub class of BrickMigration to declare a new migration code

    :param version: version of this migration
    :type version: str
    :param short_description: short description of the migration
    :type short_description: str
    :param authenticate_sys_user: if True, the migration will be executed with the sys user authenticated.
                                  Can be useful to set to False when User table is changed.
    :type authenticate_sys_user: bool
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
            class_, version_obj, short_description, authenticate_sys_user))

        return class_

    return decorator
