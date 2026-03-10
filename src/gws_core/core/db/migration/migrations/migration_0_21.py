from gws_core.core.db.migration.sql_migrator import SqlMigrator
from gws_core.lab.lab_model import LabModel
from gws_core.share.shared_resource import SharedResource
from gws_core.share.shared_scenario import SharedScenario
from gws_core.user.user_service import UserService

from ....utils.logger import Logger
from ...version import Version
from ..brick_migration_decorator import brick_migration
from ..brick_migrator import BrickMigration


@brick_migration(
    "0.21.0",
    short_description="Migrate SharedResource and SharedScenario to use LabModel FK and User FK.",
)
class Migration0210(BrickMigration):
    @classmethod
    def migrate(cls, sql_migrator: SqlMigrator, from_version: Version, to_version: Version) -> None:

        LabModel.create_table()

        # Migrate data and drop old columns for both shared tables
        for shared_model in [SharedResource, SharedScenario]:
            cls._migrate_shared_table(sql_migrator, shared_model)

    @classmethod
    def _migrate_shared_table(cls, sql_migrator: SqlMigrator, shared_model: type) -> None:
        table_name = shared_model.get_table_name()

        # Check if old columns exist (migration may have already run)
        if not shared_model.column_exists("lab_name"):
            return

        # Insert distinct labs from old columns into gws_lab (ignore duplicates on lab_id+mode)
        # Since old data doesn't have mode info, we default to prod mode
        shared_model.execute_sql(
            f"""
            INSERT IGNORE INTO gws_lab (id, lab_id, name, is_current_lab, mode, environment, space_id, space_name, created_at, last_modified_at)
            SELECT DISTINCT UUID(), lab_id, lab_name, 0, 'prod', 'ON_CLOUD', space_id, space_name, NOW(), NOW()
            FROM {table_name}
            WHERE lab_id IS NOT NULL AND lab_id != ''
              AND lab_id NOT IN (SELECT gws_lab.lab_id FROM gws_lab)
            """
        )

        # Resolve user_id: import from Constellab if missing locally, fallback to system user
        sys_user = UserService.get_sysuser()
        # Get distinct user_ids that don't exist locally
        rows = (
            shared_model.get_db()
            .execute_sql(
                f"""
            SELECT DISTINCT user_id FROM {table_name}
            WHERE user_id IS NOT NULL AND user_id != ''
              AND user_id NOT IN (SELECT id FROM gws_user)
            """
            )
            .fetchall()
        )

        for (user_id,) in rows:
            try:
                UserService.get_or_import_user_info(user_id)
            except Exception:
                # User cannot be imported, fallback to system user
                Logger.warning(
                    f"Migration 0.21.0: Could not import user '{user_id}' from Constellab, "
                    f"falling back to system user for {table_name} records."
                )
                shared_model.execute_sql(
                    f"UPDATE {table_name} SET user_id = '{sys_user.id}' WHERE user_id = '{user_id}'"
                )

        # Remap lab_id from the logical lab ID to the new gws_lab UUID PK
        shared_model.execute_sql(
            f"""
            UPDATE {table_name} t
            INNER JOIN gws_lab gl ON gl.lab_id = t.lab_id
            SET t.lab_id = gl.id
            WHERE t.lab_id IS NOT NULL AND t.lab_id != ''
            """
        )

        # Set lab_id to NULL where the lab doesn't exist in gws_lab (safety net)
        shared_model.execute_sql(
            f"""
            UPDATE {table_name}
            SET lab_id = NULL
            WHERE lab_id IS NOT NULL
              AND lab_id != ''
              AND lab_id NOT IN (SELECT id FROM gws_lab)
            """
        )

        # Set empty strings to NULL for FK compatibility
        shared_model.execute_sql(f"UPDATE {table_name} SET lab_id = NULL WHERE lab_id = ''")
        shared_model.execute_sql(f"UPDATE {table_name} SET user_id = NULL WHERE user_id = ''")

        # Drop old columns that are no longer needed
        sql_migrator.drop_column_if_exists(shared_model, "lab_name")
        sql_migrator.drop_column_if_exists(shared_model, "user_firstname")
        sql_migrator.drop_column_if_exists(shared_model, "user_lastname")
        sql_migrator.drop_column_if_exists(shared_model, "space_id")
        sql_migrator.drop_column_if_exists(shared_model, "space_name")
        sql_migrator.migrate()

        # Add FK constraints on lab_id and user_id
        shared_model.create_foreign_key_if_not_exist(shared_model.lab)
        shared_model.create_foreign_key_if_not_exist(shared_model.user)
