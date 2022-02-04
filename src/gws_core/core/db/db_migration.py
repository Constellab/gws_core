from abc import abstractmethod
from typing import Callable, Dict, List, Type

from gws_core.brick.brick_helper import BrickHelper
from gws_core.brick.brick_service import BrickService
from gws_core.core.db.version import Version
from gws_core.core.utils.logger import Logger
from gws_core.core.utils.utils import Utils


class MigrationObject():
    """Simple object to store brick migration along with version
    """
    brick_migration: Type['BrickMigration']
    version: Version

    def __init__(self, migration_object: Type['BrickMigration'], version: Version) -> None:
        self.brick_migration = migration_object
        self.version = version


class BrickMigrator():
    """Object for a brick that list all the migration and run the required migration

    :raises Exception: [description]
    :raises err: [description]
    :return: [description]
    :rtype: [type]
    """
    brick_name: str
    current_brick_version: Version

    _migration_objects: List[MigrationObject]

    def __init__(self, brick_name: str, brick_version: Version) -> None:
        self.brick_name = brick_name
        self.current_brick_version = brick_version
        self._migration_objects = []

    def append_migration(self, brick_migration: Type['BrickMigration'], version: Version) -> None:

        # Check if that version was already added
        if len([x for x in self._migration_objects if x.version == version]) > 0:
            raise Exception(
                f"Error on migrator for brick '{self.brick_name}'. The migration version '{str(version)}' was already registered. ")

        self._migration_objects.append(MigrationObject(brick_migration, version))

    def migrate(self) -> None:
        # retrieve all the migration objects that have an higher version of current brick version
        to_migrate_list: List[MigrationObject] = self._get_to_migrate_list()

        if len(to_migrate_list) == 0:
            Logger.debug(f"Skipping migration for brick '{self.brick_name}' because it is up to date")
            return

        for migration_obj in to_migrate_list:
            self._call_migration(migration_obj)

    def _get_to_migrate_list(self) -> List[MigrationObject]:
        # retrieve all the migration objects that have an higher version of current brick version
        to_migrate: List[MigrationObject] = [
            x for x in self._migration_objects if x.version > self.current_brick_version]

        # sort them to migrate in order
        to_migrate.sort(key=lambda x: x.version.get_version_as_int())
        return to_migrate

    def _call_migration(self, migration_object: MigrationObject) -> None:
        Logger.info(
            f"Start migrating '{self.brick_name}' from version '{self.current_brick_version}' to version '{migration_object.version}'")

        try:
            migration_object.brick_migration.migrate(self.current_brick_version, migration_object.version)

        except Exception as err:
            Logger.error(
                f"Error during migration of brick '{self.brick_name}' from version '{self.current_brick_version}' to version '{migration_object.version}'")
            raise err

        Logger.info(
            f"Success migrating '{self.brick_name}' from version '{self.current_brick_version}' to version '{migration_object.version}'")

        self.current_brick_version = migration_object.version


class DbMigrationService:
    """Service to register all brick migrations and call them
    """

    # store the different migration object, where key is brick
    _brick_migrators: Dict[str, BrickMigrator] = {}

    @classmethod
    def migrate(cls):
        for migrator in cls._brick_migrators.values():
            migrator.migrate()

    @classmethod
    def register_migration_object(cls, brick_migration: Type['BrickMigration'], version: Version):
        brick_name = BrickHelper.get_brick_name(brick_migration)

        if not brick_name in cls._brick_migrators:
            # TODO retrieve version of brick !
            cls._brick_migrators[brick_name] = BrickMigrator(brick_name, Version('1.0.0'))

        cls._brick_migrators[brick_name].append_migration(brick_migration, version)


class BrickMigration():

    @classmethod
    @abstractmethod
    def migrate(cls, from_version: Version, to_version: Version) -> None:
        """Must override this method to write the migration code

        :param from_version: previous version
        :type from_version: Version
        """


def brick_migration(version: str) -> Callable:
    """Decorator to place on sub class of BrickMigration to declare  a new migration code

    :param version: version of this migration
    :type version: str
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

            # Register the migration
            DbMigrationService.register_migration_object(class_, version_obj)
        except:
            BrickService.log_brick_error(
                class_,
                f"The version '{version}' used in brick_migration decorator on class '{class_.__name__}' is invalid")
            return class_

        return class_

    return decorator
