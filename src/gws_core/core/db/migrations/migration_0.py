# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from typing import Dict, List

from gws_core.brick.brick_helper import BrickHelper
from gws_core.core.db.sql_migrator import SqlMigrator
from gws_core.experiment.experiment import Experiment
from gws_core.experiment.experiment_enums import ExperimentType
from gws_core.impl.file.fs_node_model import FSNodeModel
from gws_core.impl.table.table import Table
from gws_core.lab.lab_config_model import LabConfigModel
from gws_core.model.typing import Typing
from gws_core.model.typing_manager import TypingManager
from gws_core.process.process_model import ProcessModel
from gws_core.protocol.protocol_model import ProtocolModel
from gws_core.report.report import Report
from gws_core.resource.resource_list_base import ResourceListBase
from gws_core.resource.resource_model import ResourceModel, ResourceOrigin
from gws_core.resource.resource_set import ResourceSet
from gws_core.resource.view_config.view_config import ViewConfig
from gws_core.tag.tag_model import TagModel
from gws_core.tag.taggable_model import TaggableModel
from gws_core.task.plug import Sink, Source
from gws_core.task.task_input_model import TaskInputModel
from gws_core.task.task_model import TaskModel
from peewee import BigIntegerField, CharField

from ...utils.logger import Logger
from ..brick_migrator import BrickMigration
from ..db_migration import brick_migration
from ..version import Version


@brick_migration('0.2.2', short_description='Adding deprecated columns to Typing')
class Migration022(BrickMigration):

    @classmethod
    def migrate(cls, from_version: Version, to_version: Version) -> None:

        migrator: SqlMigrator = SqlMigrator(Typing.get_db())

        migrator.add_column_if_not_exists(Typing, Typing.deprecated_since)
        migrator.add_column_if_not_exists(Typing, Typing.deprecated_message)
        migrator.migrate()


@brick_migration('0.2.3', short_description='Create LabConfigModel table and add lab_config_id to experiment')
class Migration023(BrickMigration):

    @classmethod
    def migrate(cls, from_version: Version, to_version: Version) -> None:
        LabConfigModel.create_table()

        migrator: SqlMigrator = SqlMigrator(Experiment.get_db())

        migrator.add_column_if_not_exists(Experiment, Experiment.lab_config)
        migrator.migrate()


@brick_migration('0.3.3', short_description='Create symbolic link in FsNodeModel and convert size to BigInt')
class Migration033(BrickMigration):

    @classmethod
    def migrate(cls, from_version: Version, to_version: Version) -> None:
        migrator: SqlMigrator = SqlMigrator(Typing.get_db())

        migrator.add_column_if_not_exists(FSNodeModel, FSNodeModel.is_symbolic_link)
        migrator.alter_column_type(FSNodeModel, FSNodeModel.size.column_name, BigIntegerField(null=True))
        migrator.migrate()


@brick_migration('0.3.8', short_description='Create lab config column in report table')
class Migration038(BrickMigration):

    @classmethod
    def migrate(cls, from_version: Version, to_version: Version) -> None:

        migrator: SqlMigrator = SqlMigrator(Report.get_db())

        migrator.add_column_if_not_exists(Report, Report.lab_config)
        migrator.migrate()


@brick_migration('0.3.9', short_description='Refactor io specs, add brick_version to process')
class Migration039(BrickMigration):

    @classmethod
    def migrate(cls, from_version: Version, to_version: Version) -> None:

        migrator: SqlMigrator = SqlMigrator(Typing.get_db())

        migrator.add_column_if_not_exists(Typing, Typing.brick_version)
        migrator.add_column_if_not_exists(TaskModel, TaskModel.brick_version)
        migrator.add_column_if_not_exists(ProtocolModel, ProtocolModel.brick_version)
        migrator.migrate()

        process_model_list: List[ProcessModel] = list(TaskModel.select()) + list(ProtocolModel.select())
        for process_model in process_model_list:

            try:
                output_resources: Dict[str, ResourceModel] = {}
                for port_name, port in process_model.outputs.ports.items():
                    output_resources[port_name] = port.resource_model

                input_resources: Dict[str, ResourceModel] = {}
                for port_name, port in process_model.inputs.ports.items():
                    input_resources[port_name] = port.resource_model

                # update io specs
                process_model.set_process_type(process_model.process_typing_name)

                # set port output from output_resources
                for port_name, port in process_model.outputs.ports.items():
                    if port_name in output_resources:
                        port.resource_model = output_resources[port_name]
                process_model.data["outputs"] = process_model.outputs.to_json()

                # set port input from input_resources
                for port_name, port in process_model.inputs.ports.items():
                    if port_name in input_resources:
                        port.resource_model = input_resources[port_name]

                process_model.data["inputs"] = process_model.inputs.to_json()

                # set brick version
                typing = TypingManager.get_typing_from_name_and_check(process_model.process_typing_name)
                process_model.brick_version = BrickHelper.get_brick_version(typing.brick)
                process_model.save()
            except Exception as err:
                Logger.error(f'Error while migrating process {process_model.id} : {err}')
                Logger.log_exception_stack_trace(err)


@brick_migration('0.3.10', short_description='Add source config in TaskModel - Add order to TagModel - Update tags columns content')
class Migration0310(BrickMigration):

    @classmethod
    def migrate(cls, from_version: Version, to_version: Version) -> None:

        migrator: SqlMigrator = SqlMigrator(Typing.get_db())

        migrator.add_column_if_not_exists(TaskModel, TaskModel.source_config_id)
        migrator.add_column_if_not_exists(TagModel, TagModel.order)
        migrator.migrate()

        task_models: List[TaskModel] = list(TaskModel.select().where(
            TaskModel.process_typing_name == Source._typing_name))

        # Update source config in task models
        for task_model in task_models:
            resource_id = Source.get_resource_id_from_config(task_model.config.get_values())

            if resource_id is not None:
                resource: ResourceModel = ResourceModel.get_by_id(resource_id)
                task_model.source_config_id = resource.id if resource is not None else None
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


@brick_migration('0.3.12', short_description='Add parent resource to resource model')
class Migration0312(BrickMigration):
    @classmethod
    def migrate(cls, from_version: Version, to_version: Version) -> None:
        migrator: SqlMigrator = SqlMigrator(ResourceModel.get_db())

        migrator.add_column_if_not_exists(ResourceModel, ResourceModel.parent_resource_id)
        migrator.migrate()

        # Set the parent id for resource inside ResourceSet

        # retrieve all resource of type  ResourceListBase or children
        resource_models: List[ResourceModel] = list(ResourceModel.select_by_type_and_sub_types(ResourceListBase))
        for resource_model in resource_models:

            try:
                resource_set: ResourceSet = resource_model.get_resource()

                # loop through children to set the parent resource
                children_resources = resource_set._get_all_resource_models()
                for child_resource_model in children_resources:
                    # update the parent only if the resource was created by the same task than parent (meaning it was created with the resource set)
                    if resource_model.task_model == child_resource_model.task_model:
                        child_resource_model.parent_resource_id = resource_model
                        child_resource_model.save()
            except Exception as err:
                Logger.error(f'Error while migrating resource {resource_model.id} : {err}')
                Logger.log_exception_stack_trace(err)


@brick_migration('0.3.13', short_description='Update orgin values of resources, add show_in_databox and generated_by_port_name columns. Add validated info to experiment and report')
class Migration0313(BrickMigration):

    @classmethod
    def migrate(cls, from_version: Version, to_version: Version) -> None:

        migrator: SqlMigrator = SqlMigrator(ResourceModel.get_db())

        migrator.add_column_if_not_exists(ResourceModel, ResourceModel.show_in_databox)
        migrator.add_column_if_not_exists(ResourceModel, ResourceModel.generated_by_port_name)
        migrator.add_column_if_not_exists(Experiment, Experiment.validated_at)
        migrator.add_column_if_not_exists(Experiment, Experiment.validated_by)
        migrator.add_column_if_not_exists(Report, Report.validated_at)
        migrator.add_column_if_not_exists(Report, Report.validated_by)
        migrator.migrate()

        # retrieve all resource of type  ResourceListBase or children
        resource_models: List[ResourceModel] = list(ResourceModel.select())
        for resource_model in resource_models:

            try:
                # update orgin values
                if resource_model.experiment is not None:
                    if resource_model.experiment.type == ExperimentType.IMPORTER:
                        resource_model.origin = ResourceOrigin.IMPORTED
                    elif resource_model.experiment.type == ExperimentType.TRANSFORMER:
                        resource_model.origin = ResourceOrigin.TRANSFORMED

                # set show_in_databox
                task_input_model: TaskInputModel = TaskInputModel.get_by_resource_model(resource_model.id).first()
                # if the resource is used a input of a Sink task or the resource was uploaded
                if (task_input_model is not None and task_input_model.task_model.process_typing_name == Sink._typing_name) or \
                        resource_model.origin == ResourceOrigin.UPLOADED:
                    resource_model.show_in_databox = True

                # set generated by port name
                if resource_model.task_model is not None:
                    # If this is a child resource, take the parent id as generated by port name
                    resource_model_id = resource_model.id if resource_model.parent_resource_id is None else resource_model.parent_resource_id
                    # loop thourgh task output and check if the resource correspond to the resource in the port
                    for port_name, port in resource_model.task_model.outputs.ports.items():
                        if port.resource_model and port.resource_model.id == resource_model_id:
                            resource_model.generated_by_port_name = port_name
                            break

                resource_model.save()

            except Exception as err:
                Logger.error(f'Error while migrating resource {resource_model.id} : {err}')
                Logger.log_exception_stack_trace(err)

        # update validated info to experiment and report
        experiment_models: List[Experiment] = list(Experiment.select())
        for experiment_model in experiment_models:
            if experiment_model.is_validated:
                experiment_model.validated_at = experiment_model.last_modified_at
                experiment_model.validated_by = experiment_model.last_modified_by
                experiment_model.save()

        report_models: List[Report] = list(Report.select())
        for report_model in report_models:
            if report_model.is_validated:
                report_model.validated_at = report_model.last_modified_at
                report_model.validated_by = report_model.last_modified_by
                report_model.save()


@brick_migration('0.3.14', short_description='Update table meta (tags)')
class Migration0314(BrickMigration):
    @classmethod
    def migrate(cls, from_version: Version, to_version: Version) -> None:

        resource_models: List[ResourceModel] = list(ResourceModel.get_by_types_and_sub([Table._typing_name]))

        for resource_model in resource_models:
            try:
                table: Table = resource_model.get_resource()

                changed: bool = False
                if len(table.get_column_tags()) == 0:
                    table.set_all_columns_tags(table._meta['column_tags'])
                    changed = True

                if len(table.get_row_tags()) == 0:
                    table.set_all_rows_tags(table._meta['row_tags'])
                    changed = True

                if changed:
                    table._meta = None
                    resource_model.receive_fields_from_resource(table)
                    resource_model.save()

            except Exception as err:
                Logger.error(f'Error while migrating resource {resource_model.id} : {err}')
                Logger.log_exception_stack_trace(err)


@brick_migration('0.3.15', short_description='Add last_sync info to Experiment and Report')
class Migration0315(BrickMigration):

    @classmethod
    def migrate(cls, from_version: Version, to_version: Version) -> None:

        migrator: SqlMigrator = SqlMigrator(Experiment.get_db())
        migrator.add_column_if_not_exists(Experiment, Experiment.last_sync_at)
        migrator.add_column_if_not_exists(Experiment, Experiment.last_sync_by)
        migrator.add_column_if_not_exists(Report, Report.last_sync_at)
        migrator.add_column_if_not_exists(Report, Report.last_sync_by)
        migrator.migrate()

        experiments: List[Experiment] = list(Experiment.select().where(Experiment.is_validated == True))
        for experiment in experiments:
            experiment.last_sync_at = experiment.last_modified_at
            experiment.last_sync_by = experiment.last_modified_by
            experiment.save()

        reports: List[Report] = list(Report.select().where(Report.is_validated == True))
        for report in reports:
            report.last_sync_at = report.last_modified_at
            report.last_sync_by = report.last_modified_by
            report.save()


@brick_migration('0.3.16', short_description='Add tag to ViewConfig. Set tag length to varchar 255')
class Migration0316(BrickMigration):

    @classmethod
    def migrate(cls, from_version: Version, to_version: Version) -> None:

        migrator: SqlMigrator = SqlMigrator(ViewConfig.get_db())

        migrator.add_column_if_not_exists(ViewConfig, ViewConfig.tags)
        migrator.add_column_if_not_exists(ViewConfig, ViewConfig.flagged)
        migrator.alter_column_type(Experiment, Experiment.tags.column_name, CharField(null=True, max_length=255))
        migrator.alter_column_type(ResourceModel, ResourceModel.tags.column_name, CharField(null=True, max_length=255))
        migrator.migrate()
