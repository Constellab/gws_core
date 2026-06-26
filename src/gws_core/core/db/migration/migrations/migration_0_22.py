from peewee import CharField, TextField

from gws_core.config.config import Config
from gws_core.core.db.migration.sql_migrator import SqlMigrator
from gws_core.core.model.db_field import SerializableDBField
from gws_core.core.model.model_with_user import ModelWithUser
from gws_core.credentials.credentials import Credentials
from gws_core.form.form import Form
from gws_core.form_template.form_template import FormTemplate
from gws_core.form_template.form_template_version import FormTemplateVersion
from gws_core.model.typing import Typing
from gws_core.note.note import Note
from gws_core.note_template.note_template import NoteTemplate
from gws_core.process.process_model import ProcessModel
from gws_core.progress_bar.progress_bar import ProgressBar
from gws_core.protocol.protocol_layout import ProtocolLayout
from gws_core.protocol.protocol_model import ProtocolModel
from gws_core.resource.resource_model import ResourceModel
from gws_core.resource.view_config.view_config import ViewConfig
from gws_core.scenario.scenario import Scenario
from gws_core.scenario_template.scenario_template import ScenarioTemplate
from gws_core.share.share_link import ShareLink
from gws_core.task.task_model import TaskModel
from gws_core.triggered_job.triggered_job_model import TriggeredJobModel
from gws_core.user.user_service import UserService

from ....utils.logger import Logger
from ...version import Version
from ..brick_migration_decorator import brick_migration
from ..brick_migrator import BrickMigration


@brick_migration(
    "0.22.1",
    short_description="Add definition_errors column to Typing",
)
class Migration0221(BrickMigration):
    @classmethod
    def migrate(cls, sql_migrator: SqlMigrator, from_version: Version, to_version: Version) -> None:
        Logger.info("Migration 0.22.1: Adding definition_errors column to Typing")
        sql_migrator.add_column_if_not_exists(Typing, Typing.definition_errors)
        sql_migrator.migrate()


# All concrete models that extend ModelWithUser. Their created_by_id and
# last_modified_by_id columns were created nullable but the model now declares
# them as NOT NULL (TypedForeignKeyField), so existing app databases must be
# backfilled and the columns altered to NOT NULL.
_MODELS_WITH_USER: list[type[ModelWithUser]] = [
    Config,
    Credentials,
    Form,
    FormTemplate,
    FormTemplateVersion,
    Note,
    NoteTemplate,
    ProtocolModel,
    ResourceModel,
    Scenario,
    ScenarioTemplate,
    ShareLink,
    TaskModel,
    TriggeredJobModel,
    ViewConfig,
]

_USER_FK_COLUMNS = ["created_by_id", "last_modified_by_id"]


# Concrete ProcessModel tables. Their instance_name, name, data, scenario_id
# and progress_bar columns were created nullable but the model now declares
# them NOT NULL (TypedCharField/TypedJSONField/TypedForeignKeyField), so
# existing app databases must be backfilled and the columns altered to NOT NULL.
_PROCESS_MODELS: list[type[ProcessModel]] = [TaskModel, ProtocolModel]


# Maps the old CredentialsType enum value to the new brick-namespaced registry id.
# The CredentialsType enum was replaced by a decorator-based registry, so the
# gws_credentials.type column now stores the registered data class id
# (e.g. 'gws_core.s3') instead of the old enum value (e.g. 'S3').
_CREDENTIALS_TYPE_MIGRATION = {
    "BASIC": "gws_core.basic",
    "S3": "gws_core.s3",
    "S3_LAB_SERVER": "gws_core.s3_lab_server",
    "LAB": "gws_core.lab",
    "OTHER": "gws_core.other",
}


@brick_migration(
    "0.22.2",
    short_description="Set created_by and last_modified_by to NOT NULL on all ModelWithUser tables,"
    " migrate credentials type to namespaced registry id,"
    " set instance_name/name/data/scenario_id/progress_bar to NOT NULL on process tables,"
    " set parent_protocol_id to NOT NULL on the gws_task table,"
    " and set the gws_protocol layout column to NOT NULL",
)
class Migration0222(BrickMigration):
    @classmethod
    def migrate(cls, sql_migrator: SqlMigrator, from_version: Version, to_version: Version) -> None:
        cls._migrate_user_columns(sql_migrator)
        cls._migrate_credentials_type()
        cls._migrate_process_columns(sql_migrator)
        cls._migrate_protocol_layout(sql_migrator)

    @classmethod
    def _migrate_protocol_layout(cls, sql_migrator: SqlMigrator) -> None:
        """Backfill NULL gws_protocol.layout columns with an empty layout and set the
        column to NOT NULL, mirroring the model which now always initializes a layout."""
        if not ProtocolModel.table_exists() or not ProtocolModel.column_exists("layout"):
            Logger.info("Migration 0.22.2: No gws_protocol.layout column, skipping")
            return

        empty_layout = ProtocolLayout().serialize()
        Logger.info("Migration 0.22.2: Backfilling NULL gws_protocol.layout columns")
        ProtocolModel.execute_sql(
            f"UPDATE [TABLE_NAME] SET layout = '{empty_layout}' WHERE layout IS NULL"
        )

        Logger.info("Migration 0.22.2: Setting gws_protocol.layout to NOT NULL")
        sql_migrator.alter_column_type(
            ProtocolModel, "layout", SerializableDBField(ProtocolLayout, null=False)
        )
        sql_migrator.migrate()

    @classmethod
    def _migrate_user_columns(cls, sql_migrator: SqlMigrator) -> None:
        sys_user = UserService.get_sysuser()

        for model in _MODELS_WITH_USER:
            table_name = model.get_table_name()

            # Skip models whose table does not exist yet (fresh DB)
            if not model.table_exists():
                Logger.info(f"Migration 0.22.2: Table '{table_name}' does not exist, skipping")
                continue

            # Only act on columns that already exist and are still nullable
            existing_columns = [c for c in _USER_FK_COLUMNS if model.column_exists(c)]
            if not existing_columns:
                Logger.info(
                    f"Migration 0.22.2: No created_by/last_modified_by columns on '{table_name}', skipping"
                )
                continue

            Logger.info(
                f"Migration 0.22.2: Backfilling NULL user columns on '{table_name}'"
            )

            # Backfill NULLs, preferring the sibling column when it is set,
            # falling back to the system user otherwise.
            if "created_by_id" in existing_columns:
                model.execute_sql(
                    f"UPDATE {table_name} SET created_by_id = COALESCE(last_modified_by_id, '{sys_user.id}') "
                    "WHERE created_by_id IS NULL"
                )
            if "last_modified_by_id" in existing_columns:
                model.execute_sql(
                    f"UPDATE {table_name} SET last_modified_by_id = COALESCE(created_by_id, '{sys_user.id}') "
                    "WHERE last_modified_by_id IS NULL"
                )

            # Set the columns to NOT NULL
            Logger.info(
                f"Migration 0.22.2: Setting user columns to NOT NULL on '{table_name}'"
            )
            for column in existing_columns:
                sql_migrator.alter_column_type(
                    model, column, CharField(max_length=36, null=False)
                )
            sql_migrator.migrate()

    @classmethod
    def _migrate_credentials_type(cls) -> None:
        if not Credentials.table_exists():
            return

        Logger.info(
            "Migration 0.22.2: Migrating credentials type to namespaced registry id"
        )
        for old_type, new_type in _CREDENTIALS_TYPE_MIGRATION.items():
            Credentials.execute_sql(
                f"UPDATE [TABLE_NAME] SET type = '{new_type}' WHERE type = '{old_type}'"
            )

    @classmethod
    def _migrate_process_columns(cls, sql_migrator: SqlMigrator) -> None:
        for model in _PROCESS_MODELS:
            table_name = model.get_table_name()

            # Skip models whose table does not exist yet (fresh DB)
            if not model.table_exists():
                Logger.info(f"Migration 0.22.2: Table '{table_name}' does not exist, skipping")
                continue

            cls._migrate_process_model_columns(sql_migrator, model)

    @classmethod
    def _migrate_process_model_columns(
        cls, sql_migrator: SqlMigrator, model: type[ProcessModel]
    ) -> None:
        table_name = model.get_table_name()

        # scenario_id has no safe synthetic value: a process row without a
        # scenario cannot be pointed at a real one, so fail loudly rather than
        # corrupt or delete data. The operator must resolve orphan rows first.
        if model.column_exists("scenario_id"):
            cursor = model.get_db().execute_sql(
                f"SELECT COUNT(*) FROM {table_name} WHERE scenario_id IS NULL"
            )
            orphan_count = cursor.fetchone()[0]
            if orphan_count:
                raise Exception(
                    f"Migration 0.22.2: cannot set scenario_id to NOT NULL on '{table_name}': "
                    f"{orphan_count} row(s) have a NULL scenario_id. Resolve these rows before upgrading."
                )

        # parent_protocol_id is NOT NULL only on TaskModel (a task always lives
        # inside a protocol); ProtocolModel keeps it nullable for root protocols.
        # Like scenario_id it has no safe synthetic value, so fail loudly rather
        # than corrupt or delete data. The operator must resolve orphan rows first.
        if model is TaskModel and model.column_exists("parent_protocol_id"):
            cursor = model.get_db().execute_sql(
                f"SELECT COUNT(*) FROM {table_name} WHERE parent_protocol_id IS NULL"
            )
            orphan_count = cursor.fetchone()[0]
            if orphan_count:
                raise Exception(
                    f"Migration 0.22.2: cannot set parent_protocol_id to NOT NULL on '{table_name}': "
                    f"{orphan_count} row(s) have a NULL parent_protocol_id. Resolve these rows before upgrading."
                )

        # progress_bar_id has no safe synthetic SQL default, so create a fresh
        # ProgressBar for every orphan row (mirroring ProcessFactory) before
        # altering the column.
        if model.column_exists("progress_bar_id"):
            cls._backfill_progress_bars(model)

        cls._backfill_process_columns(model)
        cls._alter_process_columns(sql_migrator, model)
        sql_migrator.migrate()

    @classmethod
    def _backfill_process_columns(cls, model: type[ProcessModel]) -> None:
        """Backfill the columns that have a safe synthetic default before altering them."""
        Logger.info(
            f"Migration 0.22.2: Backfilling NULL columns on '{model.get_table_name()}'"
        )
        if model.column_exists("data"):
            model.execute_sql("UPDATE [TABLE_NAME] SET data = '{}' WHERE data IS NULL")
        if model.column_exists("instance_name"):
            model.execute_sql(
                "UPDATE [TABLE_NAME] SET instance_name = COALESCE(name, id) "
                "WHERE instance_name IS NULL"
            )
        # name falls back to instance_name (just backfilled above) then id.
        if model.column_exists("name"):
            model.execute_sql(
                "UPDATE [TABLE_NAME] SET name = COALESCE(instance_name, id) "
                "WHERE name IS NULL"
            )

    @classmethod
    def _alter_process_columns(
        cls, sql_migrator: SqlMigrator, model: type[ProcessModel]
    ) -> None:
        """Alter the previously-backfilled columns to NOT NULL."""
        Logger.info(
            "Migration 0.22.2: Setting instance_name/name/data/scenario_id/progress_bar"
            f" to NOT NULL on '{model.get_table_name()}'"
        )
        if model.column_exists("instance_name"):
            sql_migrator.alter_column_type(
                model, "instance_name", CharField(max_length=255, null=False)
            )
        if model.column_exists("name"):
            sql_migrator.alter_column_type(
                model, "name", CharField(max_length=255, null=False)
            )
        if model.column_exists("data"):
            sql_migrator.alter_column_type(model, "data", TextField(null=False))
        if model.column_exists("scenario_id"):
            sql_migrator.alter_column_type(
                model, "scenario_id", CharField(max_length=36, null=False)
            )
        if model.column_exists("progress_bar_id"):
            sql_migrator.alter_column_type(
                model, "progress_bar_id", CharField(max_length=36, null=False)
            )
        # parent_protocol_id is NOT NULL only on TaskModel (see orphan check above).
        if model is TaskModel and model.column_exists("parent_protocol_id"):
            sql_migrator.alter_column_type(
                model, "parent_protocol_id", CharField(max_length=36, null=False)
            )

    @classmethod
    def _backfill_progress_bars(cls, model: type[ProcessModel]) -> None:
        """Create a fresh ProgressBar for every process row that has none, mirroring
        the way ProcessFactory always attaches a progress bar to a process."""
        table_name = model.get_table_name()

        orphans: list[ProcessModel] = list(
            model.select().where(model.progress_bar.is_null(True))
        )
        if not orphans:
            Logger.info(f"Migration 0.22.2: No NULL progress_bar_id on '{table_name}'")
            return

        Logger.info(
            f"Migration 0.22.2: Backfilling {len(orphans)} NULL progress_bar_id on '{table_name}'"
        )
        for process_model in orphans:
            progress_bar = ProgressBar(
                process_id=process_model.id,
                process_typing_name=process_model.process_typing_name,
            )
            progress_bar.save()
            process_model.progress_bar = progress_bar
            process_model.save(skip_hook=True)
