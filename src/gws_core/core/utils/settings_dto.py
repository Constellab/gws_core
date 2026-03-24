from datetime import datetime, timezone

from typing_extensions import TypedDict

from gws_core.core.model.model_dto import BaseModelDTO


class SettingsDTO(BaseModelDTO):
    lab_id: str
    lab_name: str
    space_api_url: str | None
    lab_prod_api_url: str
    lab_dev_api_url: str
    lab_environment: str
    virtual_host: str
    main_settings_file_path: str
    log_dir: str
    data_dir: str
    file_store_dir: str
    kv_store_dir: str
    data: dict


class ModuleInfo(TypedDict):
    path: str
    name: str
    source: str
    error: str | None


class BrickMigrationLogHistory(BaseModelDTO):
    version: str | None
    migration_date: str


class BrickMigrationLog(BaseModelDTO):
    version: str | None
    last_date_check: str | None
    history: list[BrickMigrationLogHistory]


class BrickMigrationsLogs(BaseModelDTO):
    """Container for all brick migration logs, keyed by brick_name."""

    # dict[brick_name, BrickMigrationLog]
    bricks: dict[str, BrickMigrationLog] = {}

    def get_brick_migration_log(self, brick_name: str) -> BrickMigrationLog | None:
        """Get a brick migration log for the specified brick.

        :param brick_name: Name of the brick
        :type brick_name: str
        :return: The brick migration log or None
        :rtype: BrickMigrationLog | None
        """
        return self.bricks.get(brick_name)

    def has_any_migration_log(self) -> bool:
        """Check if any brick has a migration log.

        :return: True if at least one brick has a log
        :rtype: bool
        """
        return len(self.bricks) > 0

    def set_brick_version(self, brick_name: str, version: str) -> None:
        """Set the current version and last_date_check for a brick.
        Does not add a history entry. Use this to record the current state without
        indicating an actual migration was run.

        :param brick_name: Name of the brick
        :type brick_name: str
        :param version: Version of the brick
        :type version: str
        """
        brick_migration = self._get_or_create_log(brick_name)
        date = datetime.now(timezone.utc).isoformat()

        brick_migration.last_date_check = date
        brick_migration.version = version

    def add_migration_history(self, brick_name: str, version: str) -> None:
        """Record that an actual migration was run for a brick.
        Updates the version, last_date_check and appends a history entry.

        :param brick_name: Name of the brick
        :type brick_name: str
        :param version: Version migrated to
        :type version: str
        """
        brick_migration = self._get_or_create_log(brick_name)
        date = datetime.now(timezone.utc).isoformat()

        brick_migration.last_date_check = date
        brick_migration.version = version
        brick_migration.history.append(
            BrickMigrationLogHistory(version=version, migration_date=date)
        )

    def _get_or_create_log(self, brick_name: str) -> BrickMigrationLog:
        """Get or create a BrickMigrationLog for the specified brick."""
        if brick_name not in self.bricks:
            self.bricks[brick_name] = BrickMigrationLog(
                version=None,
                history=[],
                last_date_check=None,
            )

        return self.bricks[brick_name]

    def save_as_json(self) -> dict:
        """Get the migration logs in a JSON-serializable format."""
        return self.to_json_dict()["bricks"]


class PipPackage(BaseModelDTO):
    name: str
    version: str
