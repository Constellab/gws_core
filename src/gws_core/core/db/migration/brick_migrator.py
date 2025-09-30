
from abc import abstractmethod
from typing import List, Type

from gws_core.core.db.db_manager import AbstractDbManager
from gws_core.core.db.migration.migration_dto import MigrationDTO
from gws_core.core.db.migration.sql_migrator import SqlMigrator
from gws_core.core.db.version import Version
from gws_core.core.utils.logger import Logger
from gws_core.user.current_user_service import AuthenticateUser

from ...exception.exceptions import BadRequestException


class BrickMigration():

    @classmethod
    @abstractmethod
    def migrate(cls,
                sql_migrator: SqlMigrator,
                from_version: Version,
                to_version: Version) -> None:
        """Must override this class method to write the migration code

        The class must be decorated with @brick_migration decorator to be executed. The version
        used in the @brick_migration must be unique, there can't be 2 migration with the same version for the same brick

        :param sql_migrator: The SqlMigrator object to use to make SQL requests for the provided DbManager
        :type sql_migrator: SqlMigrator
        :param from_version: previous version
        :type from_version: Version
        :param to_version: version to migrate to
        :type to_version: Version
        """


class MigrationObject():
    """Simple object to store brick migration along with version
    """
    brick_migration: Type['BrickMigration']
    version: Version
    short_description: str
    authenticate_sys_user: bool
    db_manager_type: Type[AbstractDbManager]

    def __init__(self, brick_migration: Type['BrickMigration'], version: Version, short_description: str,
                 authenticate_sys_user: bool, db_manager_type: Type[AbstractDbManager]) -> None:
        self.brick_migration = brick_migration
        self.version = version
        self.short_description = short_description
        self.authenticate_sys_user = authenticate_sys_user
        self.db_manager_type = db_manager_type

    def call_migration(self, from_version: Version) -> None:
        """Call the migration

        :param from_version: previous version
        :type from_version: Version
        """

        sql_migrator = SqlMigrator(self.db_manager_type.get_db())

        if self.authenticate_sys_user:
            # Authenticate the system user if there is no current user (when calling migration on start)
            with AuthenticateUser.system_user():
                self.brick_migration.migrate(sql_migrator, from_version, self.version)
        else:
            self.brick_migration.migrate(sql_migrator, from_version, self.version)

    def get_db_unique_name(self) -> str:
        return self.db_manager_type.get_unique_name()

    def to_dto(self) -> MigrationDTO:
        return MigrationDTO(
            version=str(self.version),
            db_unique_name=self.get_db_unique_name(),
            short_description=self.short_description
        )


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

    def append_migration(self, migration_obj: MigrationObject) -> None:

        # Check if that version and db_manager was already added
        if self.has_migration_version(migration_obj.version, migration_obj.get_db_unique_name()):
            raise Exception(
                f"Error on migrator for brick '{self.brick_name}'. The migration version '{str(migration_obj.version)}' for db_manager '{migration_obj.get_db_unique_name()}' was already registered. ")

        self._migration_objects.append(migration_obj)

    def migrate(self, db_manager_type: Type[AbstractDbManager]) -> bool:
        """Migrate the brick by calling all the migration scripts for the specified db_manager.
        If there were not migration return false, otherwise True

        :param db_manager_type: The AbstractDbManager type to filter migrations
        :type db_manager_type: Type[AbstractDbManager]
        :return: _description_
        :rtype: bool
        """

        # retrieve all the migration objects that have an higher version of current brick version
        # and match the db_manager_type
        to_migrate_list: List[MigrationObject] = self._get_to_migrate_list(db_manager_type)

        if len(to_migrate_list) == 0:
            Logger.debug(
                f"Skipping migration for brick '{self.brick_name}' and DB '{db_manager_type.get_unique_name()}' because it is up to date")
            return False

        for migration_obj in to_migrate_list:
            self._call_migration(migration_obj)

        return True

    def _get_to_migrate_list(self, db_manager_type: Type[AbstractDbManager]) -> List[MigrationObject]:
        # retrieve all the migration objects that have an higher version of current brick version
        # and match the db_manager_type
        to_migrate: List[MigrationObject] = [
            x for x in self._migration_objects
            if x.version > self.current_brick_version and x.db_manager_type.get_unique_name()
            == db_manager_type.get_unique_name()]

        # sort them to migrate in order
        to_migrate.sort(key=lambda x: x.version)
        return to_migrate

    def _call_migration(self, migration_object: MigrationObject) -> None:
        Logger.info(
            f"Start migrating '{self.brick_name}' from version '{self.current_brick_version}' to version '{migration_object.version}' for DB '{migration_object.get_db_unique_name()}'. Description: {migration_object.short_description}")

        # Authenticate the system user if there is no current user (when calling migration on start)
        try:
            migration_object.call_migration(self.current_brick_version)
        except Exception as err:
            Logger.error(
                f"Error during migration of brick '{self.brick_name}' from version '{self.current_brick_version}' to version '{migration_object.version}'")

            raise err

        Logger.info(
            f"Success migrating '{self.brick_name}' from version '{self.current_brick_version}' to version '{migration_object.version}'")

        self.current_brick_version = migration_object.version

    def call_migration_manually(self, version: Version, db_unique_name: str) -> None:
        """Call migration manually for the version at any time.
        This call the migration for all the DB managers.
        """
        migration_object = self.get_migration_object(version, db_unique_name)

        if not migration_object:
            raise BadRequestException(
                f"The migration for version '{str(version)}' of db '{db_unique_name}' for brick '{self.brick_name}'  doesn't exist")

        self._call_migration(migration_object)

    def has_migration_version(self, version: Version, db_unique_name: str) -> bool:
        # Check if that version was already added
        return self.get_migration_object(version, db_unique_name) is not None

    def get_migration_object(self, version: Version, db_unique_name: str) -> MigrationObject:
        # Check if that version was already added
        migration_objects = list([x for x in self._migration_objects if x.version ==
                                 version and x.db_manager_type.get_unique_name() == db_unique_name])
        return migration_objects[0] if len(migration_objects) > 0 else None

    def get_migration_versions(self, version: Version) -> List[MigrationObject]:
        return list([x for x in self._migration_objects if x.version == version])

    def get_migration_objects(self) -> List[MigrationObject]:
        migration_object = [*self._migration_objects]
        migration_object.sort(key=lambda x: x.version)
        migration_object.reverse()
        return migration_object
