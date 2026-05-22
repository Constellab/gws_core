from gws_core.core.db.migration.sql_migrator import SqlMigrator
from gws_core.model.typing import Typing

from ....utils.logger import Logger
from ...version import Version
from ..brick_migration_decorator import brick_migration
from ..brick_migrator import BrickMigration


@brick_migration(
    "0.22.0-beta.9",
    short_description="Add definition_errors column to Typing",
)
class Migration0220Beta9(BrickMigration):
    @classmethod
    def migrate(cls, sql_migrator: SqlMigrator, from_version: Version, to_version: Version) -> None:
        Logger.info("Migration 0.22.0-beta.9: Adding definition_errors column to Typing")
        sql_migrator.add_column_if_not_exists(Typing, Typing.definition_errors)
        sql_migrator.migrate()
