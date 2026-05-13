from gws_core.brick.brick_dto import BrickInfo
from gws_core.brick.brick_helper import BrickHelper
from gws_core.brick.brick_log_service import BrickLogService
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
    def migrate(cls):
        """Migrate all bricks. Called once at startup after all databases are connected."""

        settings: Settings = Settings.get_instance()
        if settings.is_test:
            return

        migrations_logs = settings.get_brick_migrations_logs()

        brick_migrators = cls._get_brick_migrators()

        # If migration logs exist, meaning this is not the first start
        if migrations_logs.has_any_migration_log():
            for migrator in brick_migrators.values():
                migration_log = migrations_logs.get_brick_migration_log(migrator.brick_name)

                if not migration_log or not migration_log.version:
                    # New brick with no previous version, run all its migrations
                    previous_version = Version("0.0.0")
                else:
                    previous_version = Version(migration_log.version)

                migrated = migrator.migrate(previous_version)

                if migrated:
                    migrations_logs.add_migration_history(
                        migrator.brick_name,
                        str(migrator.current_brick_version),
                    )

        # save all the brick current version as last check
        bricks = BrickHelper.get_all_bricks()
        for brick in bricks.values():
            if not brick.version:
                continue
            migrations_logs.set_brick_version(brick.name, brick.version)

        settings.save_brick_migrations_logs(migrations_logs)

    @classmethod
    def _get_brick_migrators(cls) -> dict[str, BrickMigrator]:
        """Retrieve all brick migrators, one per brick.

        The BrickMigrator is a container of MigrationObjects for a given brick.
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
            if brick_migrator.has_migration_version(migration_version):
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
        cls, brick_name: str, version_str: str
    ) -> None:
        version = Version(version_str)

        brick_migrators = cls._get_brick_migrators()
        brick_migrator = brick_migrators.get(brick_name)
        if brick_migrator is None:
            raise BadRequestException(
                f"The brick '{brick_name}' does not have migration objects registered"
            )

        brick_migrator.call_migration_manually(version)

    @classmethod
    def get_brick_migration_versions(cls, brick_name: str) -> list[MigrationObject]:
        brick_migrators = cls._get_brick_migrators()
        if brick_name not in brick_migrators:
            return []

        return brick_migrators[brick_name].get_migration_objects()
