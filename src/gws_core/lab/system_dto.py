from datetime import datetime, timezone
from typing import Literal

from typing_extensions import TypedDict

from gws_core.core.model.model_dto import BaseModelDTO
from gws_core.lab.monitor.monitor_dto import MonitorFreeDiskDTO
from gws_core.user.user_dto import SpaceDict

LabEnvironment = Literal["ON_CLOUD", "DESKTOP", "LOCAL"]


class LabInfoDTO(BaseModelDTO):
    id: str
    lab_name: str
    front_version: str
    space: SpaceDict | None


class LabStatusDTO(BaseModelDTO):
    free_disk: MonitorFreeDiskDTO
    has_start_error: bool


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
    """Container for all brick migration logs, keyed by brick_name then db_manager_unique_name."""

    # dict[brick_name, dict[db_manager_unique_name, BrickMigrationLog]]
    bricks: dict[str, dict[str, BrickMigrationLog]] = {}

    def get_brick_migration_log(
        self, brick_name: str, db_manager_unique_name: str
    ) -> BrickMigrationLog | None:
        """Get a brick migration log for the specified brick and db_manager.

        :param brick_name: Name of the brick
        :type brick_name: str
        :param db_manager_unique_name: Unique name of the database manager
        :type db_manager_unique_name: str
        :return: The brick migration log or None
        :rtype: BrickMigrationLog | None
        """
        brick_logs = self.bricks.get(brick_name)
        if brick_logs is None:
            return None
        return brick_logs.get(db_manager_unique_name)

    def has_any_migration_log_for_db_manager(self, db_manager_unique_name: str) -> bool:
        """Check if any brick has a migration log for the specified db_manager.

        :param db_manager_unique_name: Unique name of the database manager
        :type db_manager_unique_name: str
        :return: True if at least one brick has a log for this db_manager
        :rtype: bool
        """
        return any(db_manager_unique_name in brick_logs for brick_logs in self.bricks.values())

    def set_brick_version(
        self, brick_name: str, version: str, db_manager_unique_name: str
    ) -> None:
        """Set the current version and last_date_check for a brick+db_manager pair.
        Does not add a history entry. Use this to record the current state without
        indicating an actual migration was run.

        :param brick_name: Name of the brick
        :type brick_name: str
        :param version: Version of the brick
        :type version: str
        :param db_manager_unique_name: Unique name of the database manager
        :type db_manager_unique_name: str
        """
        brick_migration = self._get_or_create_log(brick_name, db_manager_unique_name)
        date = datetime.now(timezone.utc).isoformat()

        brick_migration.last_date_check = date
        brick_migration.version = version

    def add_migration_history(
        self, brick_name: str, version: str, db_manager_unique_name: str
    ) -> None:
        """Record that an actual migration was run for a brick+db_manager pair.
        Updates the version, last_date_check and appends a history entry.

        :param brick_name: Name of the brick
        :type brick_name: str
        :param version: Version migrated to
        :type version: str
        :param db_manager_unique_name: Unique name of the database manager
        :type db_manager_unique_name: str
        """
        brick_migration = self._get_or_create_log(brick_name, db_manager_unique_name)
        date = datetime.now(timezone.utc).isoformat()

        brick_migration.last_date_check = date
        brick_migration.version = version
        brick_migration.history.append(
            BrickMigrationLogHistory(version=version, migration_date=date)
        )

    def _get_or_create_log(
        self, brick_name: str, db_manager_unique_name: str
    ) -> BrickMigrationLog:
        """Get or create a BrickMigrationLog for the specified brick+db_manager pair."""
        if brick_name not in self.bricks:
            self.bricks[brick_name] = {}

        brick_db_logs = self.bricks[brick_name]

        if db_manager_unique_name not in brick_db_logs:
            brick_db_logs[db_manager_unique_name] = BrickMigrationLog(
                version=None,
                history=[],
                last_date_check=None,
            )

        return brick_db_logs[db_manager_unique_name]

    def save_as_json(self) -> dict:
        """Get the migration logs in a JSON-serializable format."""
        return self.to_json_dict()["bricks"]


class PipPackage(BaseModelDTO):
    name: str
    version: str


class LabSystemConfig(BaseModelDTO):
    python_version: str
    pip_packages: list[PipPackage]


class LabStartLogFileObject(BaseModelDTO):
    progress: dict
    main_errors: list[str]
    errors: list[str]

    def has_main_errors(self) -> bool:
        return len(self.main_errors) > 0
