from gws_core.brick.brick_dto import BrickInfo
from gws_core.brick.brick_helper import BrickHelper
from gws_core.brick.brick_log_service import BrickLogService
from gws_core.core.db.abstract_db_manager import AbstractDbManager
from gws_core.core.db.migration.brick_migrator import BrickMigrator, MigrationObject
from gws_core.core.db.version import Version
from gws_core.core.exception.exceptions.bad_request_exception import BadRequestException
from gws_core.core.utils.logger import Logger
from gws_core.core.utils.settings import Settings


class DbMigrationService:
    """Service to register all brick migrations and call them"""

    # store the different migration object, where key is brick_name
    _brick_migrators: dict[str, BrickMigrator] = {}

    _migration_objects: list[MigrationObject] = []

    @classmethod
    def migrate(cls, db_manager: AbstractDbManager):
        """Migrate all bricks for the specified db_manager

        :param db_manager: The AbstractDbManager instance to migrate. Defaults to GwsCoreDbManager.
        :type db_manager: AbstractDbManager
        """

        settings: Settings = Settings.get_instance()
        db_unique_name = db_manager.get_unique_name()
        migrations_logs = settings.get_brick_migrations_logs()

        brick_migrators = cls._get_brick_migrators()

        # If migration logs exist for this db_manager, meaning this is not the first start
        if migrations_logs.has_any_migration_log_for_db_manager(db_unique_name):
            for migrator in brick_migrators.values():
                # Look up the previous version for this brick+db_manager pair
                migration_log = migrations_logs.get_brick_migration_log(
                    migrator.brick_name, db_unique_name
                )

                if not migration_log or not migration_log.version:
                    continue

                previous_version = Version(migration_log.version)
                migrated = migrator.migrate(db_manager, previous_version)

                if migrated:
                    migrations_logs.add_migration_history(
                        migrator.brick_name,
                        str(migrator.current_brick_version),
                        db_unique_name,
                    )

        # save all the brick current version as last check
        bricks = BrickHelper.get_all_bricks()
        for brick in bricks.values():
            if not brick.version:
                continue
            migrations_logs.set_brick_version(brick.name, brick.version, db_unique_name)

        settings.save_brick_migrations_logs(migrations_logs)

    @classmethod
    def _get_brick_migrators(cls) -> dict[str, BrickMigrator]:
        """Retrieve all brick migrators, one per brick.

        The BrickMigrator is a container of MigrationObjects. The previous version
        used to determine which migrations to run is resolved per db_manager at
        migration time in the migrate() method.
        """
        if cls._brick_migrators:
            return cls._brick_migrators

        brick_migrators: dict[str, BrickMigrator] = {}

        for migration_obj in cls._migration_objects:
            brick_info: BrickInfo

            try:
                brick_info = BrickHelper.get_brick_info_and_check(migration_obj.brick_migration)
            except:
                Logger.error(
                    f"Can't retrieve brick information for migration class : '{str(migration_obj.brick_migration)}'"
                )
                continue

            brick_name = brick_info.name
            current_brick_version = Version(brick_info.version)
            migration_version = migration_obj.version

            # Check that the migration version is not higher than the brick version
            if migration_version > current_brick_version:
                BrickLogService.log_brick_message(
                    brick_name=brick_name,
                    message=f"Error while registering migration for brick {brick_name}. The migration version '{str(migration_version)}' is higher than the brick version '{str(current_brick_version)}'. Skipping migration.",
                    status="ERROR",
                )
                continue

            if brick_name not in brick_migrators:
                brick_migrators[brick_name] = BrickMigrator(brick_name, current_brick_version)

            brick_migrator: BrickMigrator = brick_migrators[brick_name]

            # Check that the migration version was not already registered
            if brick_migrator.has_migration_version(
                migration_version, migration_obj.get_db_unique_name()
            ):
                BrickLogService.log_brick_message(
                    brick_name=brick_name,
                    message=f"Error while registering migration for brick {brick_name}. The migration version '{str(migration_version)}' was already registered. Skipping migration.",
                    status="ERROR",
                )
                continue

            brick_migrator.append_migration(migration_obj)

        cls._brick_migrators = brick_migrators
        return cls._brick_migrators

    @classmethod
    def register_migration_object(cls, migration_object: MigrationObject) -> None:
        cls._migration_objects.append(migration_object)

    @classmethod
    def call_migration_manually(
        cls, brick_name: str, version_str: str, db_unique_name: str
    ) -> None:
        version = Version(version_str)

        brick_migrators = cls._get_brick_migrators()
        brick_migrator = brick_migrators.get(brick_name)
        if brick_migrator is None:
            raise BadRequestException(
                f"The brick '{brick_name}' does not have migration objects registered"
            )

        brick_migrator.call_migration_manually(version, db_unique_name)

    @classmethod
    def get_brick_migration_versions(cls, brick_name: str) -> list[MigrationObject]:
        brick_migrators = cls._get_brick_migrators()
        if brick_name not in brick_migrators:
            return []

        return brick_migrators[brick_name].get_migration_objects()
