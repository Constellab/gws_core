# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com
from abc import abstractmethod
from typing import List, Type

from gws_core.core.db.version import Version
from gws_core.core.utils.logger import Logger

from ...core.exception.exceptions import BadRequestException


class BrickMigration():

    @classmethod
    @abstractmethod
    def migrate(cls, from_version: Version, to_version: Version) -> None:
        """Must override this class method to write the migration code

        The class must be decorated with @brick_migration decorator to be executed. The version
        used in the @brick_migration must be unique, there can't be 2 migration with the same version for the same brick

        :param from_version: previous version
        :type from_version: Version
        """


class MigrationObject():
    """Simple object to store brick migration along with version
    """
    brick_migration: Type['BrickMigration']
    version: Version

    def __init__(self, brick_migration: Type['BrickMigration'], version: Version) -> None:
        self.brick_migration = brick_migration
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
        if self.has_migration_version(version):
            raise Exception(
                f"Error on migrator for brick '{self.brick_name}'. The migration version '{str(version)}' was already registered. ")

        self._migration_objects.append(MigrationObject(brick_migration, version))

    def migrate(self) -> bool:
        """Migrate the brick by calling all the migration scripts. If there were not migration return false, otherwise True

        :return: _description_
        :rtype: bool
        """
        # retrieve all the migration objects that have an higher version of current brick version
        to_migrate_list: List[MigrationObject] = self._get_to_migrate_list()

        if len(to_migrate_list) == 0:
            Logger.debug(f"Skipping migration for brick '{self.brick_name}' because it is up to date")
            return False

        for migration_obj in to_migrate_list:
            self._call_migration(migration_obj)

        return True

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

    def call_migration_manually(self, version: Version) -> None:
        """Call migration manually for the version at any time
        """
        migration_object = self.get_migration_version(version)

        if migration_object is None:
            raise BadRequestException(
                f"The migration for version '{str(version)}' for brick '{self.brick_name}' doesn't exist")

        Logger.info(
            f"Start migrating manually '{self.brick_name}' from version '{self.current_brick_version}' to version '{migration_object.version}'")

        try:
            migration_object.brick_migration.migrate(self.current_brick_version, migration_object.version)

        except Exception as err:
            Logger.error(
                f"Error during manual migration of brick '{self.brick_name}' from version '{self.current_brick_version}' to version '{migration_object.version}'")
            raise err

        Logger.info(
            f"Success migrating manually  '{self.brick_name}' from version '{self.current_brick_version}' to version '{migration_object.version}'")

    def has_migration_version(self, version: Version) -> bool:
        # Check if that version was already added
        return self.get_migration_version(version) is not None

    def get_migration_version(self, version: Version) -> MigrationObject:
        # Check if that version was already added
        migration_objects = list([x for x in self._migration_objects if x.version == version])
        return migration_objects[0] if len(migration_objects) > 0 else None