# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from typing import List, Set

from gws_core.brick.brick_helper import BrickHelper
from gws_core.core.db.sql_migrator import SqlMigrator
from gws_core.core.model.model import Model
from gws_core.experiment.experiment import Experiment
from gws_core.impl.file.fs_node_model import FSNodeModel
from gws_core.lab.lab_config_model import LabConfigModel
from gws_core.model.typing import Typing
from gws_core.model.typing_manager import TypingManager
from gws_core.process.process_model import ProcessModel
from gws_core.protocol.protocol_model import ProtocolModel
from gws_core.report.report import Report
from gws_core.resource.resource_model import ResourceModel
from gws_core.tag.tag_model import TagModel
from gws_core.tag.taggable_model import TaggableModel
from gws_core.task.plug import Source
from gws_core.task.task_model import TaskModel
from gws_core.user.current_user_service import CurrentUserService
from gws_core.user.user import User
from peewee import BigIntegerField
from playhouse.migrate import MySQLMigrator, migrate

from ...utils.logger import Logger
from ..brick_migrator import BrickMigration
from ..db_migration import brick_migration
from ..version import Version


@brick_migration('0.2.2', short_description='Adding deprecated columns to Typing')
class Migration022(BrickMigration):

    @classmethod
    def migrate(cls, from_version: Version, to_version: Version) -> None:

        migrator = MySQLMigrator(Typing.get_db_manager().db)

        migrate(
            migrator.add_column(
                Typing.get_table_name(),
                Typing.deprecated_since.column_name, Typing.deprecated_since),
            migrator.add_column(
                Typing.get_table_name(),
                Typing.deprecated_message.column_name, Typing.deprecated_message),
        )


@brick_migration('0.2.3', short_description='Create LabConfigModel table and add lab_config_id to experiment')
class Migration023(BrickMigration):

    @classmethod
    def migrate(cls, from_version: Version, to_version: Version) -> None:

        Logger.info('Create LabConfigModel table and add lab_config_id to experiment')
        migrator = MySQLMigrator(Typing.get_db_manager().db)

        LabConfigModel.create_table()
        migrate(
            migrator.add_column(
                Experiment.get_table_name(),
                Experiment.lab_config.column_name, Experiment.lab_config)
        )


@brick_migration('0.3.3', short_description='Create symbolic link in FsNodeModel and convert size to BigInt')
class Migration033(BrickMigration):

    @classmethod
    def migrate(cls, from_version: Version, to_version: Version) -> None:

        Logger.info('Create symbolic link in FsNodeModel and convert size to BigInt')
        migrator = MySQLMigrator(FSNodeModel.get_db_manager().db)

        migrate(
            migrator.add_column(
                FSNodeModel.get_table_name(),
                FSNodeModel.is_symbolic_link.column_name, FSNodeModel.is_symbolic_link),

            migrator.alter_column_type(FSNodeModel.get_table_name(), FSNodeModel.size.column_name,
                                       BigIntegerField(null=True))
        )


@brick_migration('0.3.8', short_description='Create lab config column in report table')
class Migration038(BrickMigration):

    @classmethod
    def migrate(cls, from_version: Version, to_version: Version) -> None:

        Logger.info('Create lab config column in report table')
        migrator = MySQLMigrator(FSNodeModel.get_db_manager().db)

        migrate(
            migrator.add_column(
                Report.get_table_name(),
                Report.lab_config.column_name, Report.lab_config),
        )


@brick_migration('0.3.9', short_description='Refactor io specs, add brick_version to process')
class Migration039(BrickMigration):

    @classmethod
    def migrate(cls, from_version: Version, to_version: Version) -> None:

        migrator: SqlMigrator = SqlMigrator(FSNodeModel.get_db_manager().db)

        migrator.add_column_if_not_exists(Typing, Typing.brick_version)
        migrator.add_column_if_not_exists(TaskModel, TaskModel.brick_version)
        migrator.add_column_if_not_exists(ProtocolModel, ProtocolModel.brick_version)
        migrator.migrate()

        # Authenticate the system user
        CurrentUserService.set_current_user(User.get_sysuser())

        process_model_list: List[ProcessModel] = list(TaskModel.select()) + list(ProtocolModel.select())
        for process_model in process_model_list:

            try:

                # update io specs
                process_model.set_process_type(process_model.process_typing_name)

                # set brick version
                typing = TypingManager.get_typing_from_name(process_model.process_typing_name)
                process_model.brick_version = BrickHelper.get_brick_version(typing.brick)
                process_model.save()
            except Exception as err:
                Logger.error(f'Error while migrating process {process_model.id} : {err}')
                Logger.log_exception_stack_trace(err)

        CurrentUserService.set_current_user(None)


@brick_migration('0.3.10', short_description='Add source config in TaskModel - Add order to TagModel - Update tags columns content')
class Migration0310(BrickMigration):

    @classmethod
    def migrate(cls, from_version: Version, to_version: Version) -> None:

        migrator = MySQLMigrator(FSNodeModel.get_db_manager().db)

        migrate(
            migrator.add_column(
                TaskModel.get_table_name(),
                TaskModel.source_config.column_name, TaskModel.source_config),
            migrator.add_column(
                TagModel.get_table_name(),
                TagModel.order.column_name, TagModel.order),
        )

        task_models: List[TaskModel] = list(TaskModel.select().where(
            TaskModel.process_typing_name == Source._typing_name))

        # Authenticate the system user
        CurrentUserService.set_current_user(User.get_sysuser())

        # Update source config in task models
        for task_model in task_models:
            resource_id = Source.get_resource_id_from_config(task_model.config.get_values())

            if resource_id is not None:
                task_model.source_config = ResourceModel.get_by_id(resource_id)
                task_model.save()

        # Update orders in tag models and set lowercase tag names
        tag_models: List[TagModel] = list(TagModel.select())

        order = 0
        for tag_model in tag_models:
            tag_model.order = order
            order += 1

            # force lower case to current tags and convert it to array
            values = set()
            # if the migration was not already done
            if not isinstance(tag_model.data['values'], list):
                for value in tag_model.data['values'].split(TagModel.TAG_VALUES_SEPARATOR):
                    values.add(value.lower())

                tag_model.data['values'] = list(values)
                tag_model.save()

        # update taggableModel to wrap str tag with ','
        taggable_models: List[TaggableModel] = list(ResourceModel.select()) + list(Experiment.select())
        for taggable_model in taggable_models:
            taggable_model.set_tags(taggable_model.get_tags())
            taggable_model.save()

        CurrentUserService.set_current_user(None)
