from peewee import CharField

from gws_core.config.config import Config
from gws_core.core.db.migration.sql_migrator import SqlMigrator
from gws_core.core.model.model_with_user import ModelWithUser
from gws_core.credentials.credentials import Credentials
from gws_core.form.form import Form
from gws_core.form_template.form_template import FormTemplate
from gws_core.form_template.form_template_version import FormTemplateVersion
from gws_core.model.typing import Typing
from gws_core.note.note import Note
from gws_core.note_template.note_template import NoteTemplate
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


@brick_migration(
    "0.22.2",
    short_description="Set created_by and last_modified_by to NOT NULL on all ModelWithUser tables",
)
class Migration0222(BrickMigration):
    @classmethod
    def migrate(cls, sql_migrator: SqlMigrator, from_version: Version, to_version: Version) -> None:
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
