

import os
from copy import deepcopy
from json import dump
from typing import Dict, List, Type

from peewee import BigIntegerField, CharField
from peewee import Model as PeeweeModel

from gws_core.brick.brick_helper import BrickHelper
from gws_core.brick.brick_model import BrickModel
from gws_core.config.config import Config
from gws_core.core.classes.enum_field import EnumField
from gws_core.core.db.gws_core_db_manager import GwsCoreDbManager
from gws_core.core.db.sql_migrator import SqlMigrator
from gws_core.core.model.model import Model
from gws_core.core.utils.date_helper import DateHelper
from gws_core.credentials.credentials import Credentials
from gws_core.entity_navigator.entity_navigator_type import EntityType
from gws_core.experiment.experiment import Experiment
from gws_core.impl.file.file_helper import FileHelper
from gws_core.impl.file.file_r_field import FileRField
from gws_core.impl.file.file_store import FileStore
from gws_core.impl.file.fs_node import FSNode
from gws_core.impl.file.fs_node_model import FSNodeModel
from gws_core.impl.shell.pip_shell_proxy import PipShellProxy
from gws_core.impl.shell.virtual_env.venv_dto import (VEnsStatusDTO,
                                                      VEnvCreationInfo)
from gws_core.impl.shell.virtual_env.venv_service import VEnvService
from gws_core.lab.lab_config_model import LabConfigModel
from gws_core.lab.monitor.monitor import Monitor
from gws_core.model.typing import Typing
from gws_core.model.typing_manager import TypingManager
from gws_core.model.typing_style import TypingStyle
from gws_core.process.process_factory import ProcessFactory
from gws_core.process.process_model import ProcessModel
from gws_core.progress_bar.progress_bar import ProgressBar
from gws_core.project.project import Project
from gws_core.project.project_dto import ProjectLevelStatus
from gws_core.protocol.protocol_model import ProtocolModel
from gws_core.protocol_template.protocol_template import ProtocolTemplate
from gws_core.report.report import Report
from gws_core.report.report_service import ReportService
from gws_core.report.template.report_template import ReportTemplate
from gws_core.resource.r_field.r_field import BaseRField
from gws_core.resource.resource import Resource
from gws_core.resource.resource_dto import ResourceOrigin
from gws_core.resource.resource_model import ResourceModel
from gws_core.resource.resource_service import ResourceService
from gws_core.resource.resource_set.resource_list_base import ResourceListBase
from gws_core.resource.resource_set.resource_set import ResourceSet
from gws_core.resource.view_config.view_config import ViewConfig
from gws_core.space.space_service import SpaceService
from gws_core.tag.entity_tag import EntityTag
from gws_core.tag.tag_dto import EntityTagValueFormat, TagOriginType
from gws_core.tag.tag_helper import TagHelper
from gws_core.tag.tag_key_model import TagKeyModel
from gws_core.tag.tag_value_model import TagValueModel
from gws_core.tag.taggable_model import TaggableModel
from gws_core.task.plug import Sink, Source
from gws_core.task.task_input_model import TaskInputModel
from gws_core.task.task_model import TaskModel
from gws_core.user.activity.activity import Activity
from gws_core.user.activity.activity_dto import (ActivityObjectType,
                                                 ActivityType)
from gws_core.user.current_user_service import CurrentUserService
from gws_core.user.user import User

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

        migrator.add_column_if_not_exists(
            FSNodeModel, FSNodeModel.is_symbolic_link)
        migrator.alter_column_type(
            FSNodeModel, FSNodeModel.size.column_name, BigIntegerField(null=True))
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
        migrator.add_column_if_not_exists(TaskModel, TaskModel.brick_version_on_create)
        migrator.add_column_if_not_exists(
            ProtocolModel, ProtocolModel.brick_version_on_create)
        migrator.migrate()

        process_model_list: List[ProcessModel] = list(
            TaskModel.select()) + list(ProtocolModel.select())
        for process_model in process_model_list:

            try:
                output_resources: Dict[str, ResourceModel] = {}
                for port_name, port in process_model.outputs.ports.items():
                    output_resources[port_name] = port.resource_model

                input_resources: Dict[str, ResourceModel] = {}
                for port_name, port in process_model.inputs.ports.items():
                    input_resources[port_name] = port.resource_model

                # update io specs
                process_model.set_process_type(process_model.get_process_type())

                # set port output from output_resources
                for port_name, port in process_model.outputs.ports.items():
                    if port_name in output_resources:
                        port.resource_model = output_resources[port_name]
                process_model.data["outputs"] = process_model.outputs.to_dto().to_json_dict()

                # set port input from input_resources
                for port_name, port in process_model.inputs.ports.items():
                    if port_name in input_resources:
                        port.resource_model = input_resources[port_name]

                process_model.data["inputs"] = process_model.inputs.to_dto().to_json_dict()

                # set brick version
                typing = TypingManager.get_typing_from_name_and_check(
                    process_model.process_typing_name)
                process_model.brick_version_on_create = BrickHelper.get_brick_version(
                    typing.brick)
                process_model.save()
            except Exception as err:
                Logger.error(
                    f'Error while migrating process {process_model.id} : {err}')
                Logger.log_exception_stack_trace(err)


@brick_migration('0.3.10', short_description='Add source config in TaskModel - Add order to TagModel - Update tags columns content')
class Migration0310(BrickMigration):

    @classmethod
    def migrate(cls, from_version: Version, to_version: Version) -> None:

        migrator: SqlMigrator = SqlMigrator(Typing.get_db())

        migrator.add_column_if_not_exists(
            TaskModel, TaskModel.source_config_id)
        migrator.add_column_if_not_exists(TagKeyModel, TagKeyModel.order)
        migrator.migrate()

        task_models: List[TaskModel] = list(TaskModel.select().where(
            TaskModel.process_typing_name == Source._typing_name))

        # Update source config in task models
        for task_model in task_models:
            resource_id = Source.get_resource_id_from_config(
                task_model.config.get_values())

            if resource_id is not None:
                resource: ResourceModel = ResourceModel.get_by_id(resource_id)
                task_model.source_config_id = resource.id if resource is not None else None
                task_model.save()

        # Update orders in tag models and set lowercase tag names
        tag_models: List[TagKeyModel] = list(TagKeyModel.select())

        order = 0
        raise Exception('This migration is not supported anymore')
        # for tag_model in tag_models:
        #     tag_model.order = order
        #     order += 1

        #     # force lower case to current tags and convert it to array
        #     values = set()
        #     # if the migration was not already done
        #     if not isinstance(tag_model.data['values'], list):
        #         for value in tag_model.data['values'].split(','):
        #             values.add(value.lower())

        #         tag_model.data['values'] = list(values)
        #         tag_model.save()


@brick_migration('0.3.12', short_description='Add parent resource to resource model')
class Migration0312(BrickMigration):
    @classmethod
    def migrate(cls, from_version: Version, to_version: Version) -> None:
        migrator: SqlMigrator = SqlMigrator(ResourceModel.get_db())

        migrator.add_column_if_not_exists(
            ResourceModel, ResourceModel.parent_resource_id)
        migrator.migrate()

        # Set the parent id for resource inside ResourceSet

        # retrieve all resource of type  ResourceListBase or children
        resource_models: List[ResourceModel] = list(
            ResourceModel.select_by_type_and_sub_types(ResourceListBase))
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
                Logger.error(
                    f'Error while migrating resource {resource_model.id} : {err}')
                Logger.log_exception_stack_trace(err)


@brick_migration('0.3.13', short_description='Update orgin values of resources, add show_in_databox and generated_by_port_name columns. Add validated info to experiment and report')
class Migration0313(BrickMigration):

    @classmethod
    def migrate(cls, from_version: Version, to_version: Version) -> None:

        migrator: SqlMigrator = SqlMigrator(ResourceModel.get_db())

        migrator.add_column_if_not_exists(ResourceModel, ResourceModel.flagged)
        migrator.add_column_if_not_exists(
            ResourceModel, ResourceModel.generated_by_port_name)
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
                # if resource_model.experiment is not None:
                #     if resource_model.experiment.type == ExperimentType.IMPORTER:
                #         resource_model.origin = ResourceOrigin.GENERATED
                #     elif resource_model.experiment.type == ExperimentType.TRANSFORMER:
                #         resource_model.origin = ResourceOrigin.GENERATED

                # set show_in_databox
                task_input_model: TaskInputModel = TaskInputModel.get_by_resource_model(
                    resource_model.id).first()
                # if the resource is used a input of a Sink task or the resource was uploaded
                if (task_input_model is not None and task_input_model.task_model.process_typing_name == Sink._typing_name) or \
                        resource_model.origin == ResourceOrigin.UPLOADED:
                    resource_model.flagged = True

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
                Logger.error(
                    f'Error while migrating resource {resource_model.id} : {err}')
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
        pass
        # migration deprecated, tags are now stored in the resource model


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

        experiments: List[Experiment] = list(
            Experiment.select().where(Experiment.is_validated == True))
        for experiment in experiments:
            experiment.last_sync_at = experiment.last_modified_at
            experiment.last_sync_by = experiment.last_modified_by
            experiment.save()

        reports: List[Report] = list(
            Report.select().where(Report.is_validated == True))
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
        migrator.add_column_if_not_exists(ViewConfig, ViewConfig.is_favorite)
        migrator.rename_column_if_exists(
            ResourceModel, 'show_in_databox', 'flagged')
        migrator.alter_column_type(
            Experiment, Experiment.tags.column_name, CharField(null=True, max_length=255))
        migrator.alter_column_type(
            ResourceModel, ResourceModel.tags.column_name, CharField(null=True, max_length=255))
        migrator.migrate()


@brick_migration('0.3.18', short_description='Add layout to ProtocolModel. Refactor project')
class Migration0318(BrickMigration):

    @classmethod
    def migrate(cls, from_version: Version, to_version: Version) -> None:

        migrator: SqlMigrator = SqlMigrator(ProtocolModel.get_db())
        migrator.add_column_if_not_exists(ProtocolModel, ProtocolModel.layout)
        migrator.add_column_if_not_exists(Project, Project.code)
        migrator.add_column_if_not_exists(Project, Project.parent)
        migrator.drop_column_if_exists(Project, 'description')
        migrator.migrate()


@brick_migration('0.4.1', short_description='Add started_at and finished_at to ProcessModel, refactor progress bar')
class Migration041(BrickMigration):

    @classmethod
    def migrate(cls, from_version: Version, to_version: Version) -> None:

        migrator: SqlMigrator = SqlMigrator(ProcessModel.get_db())
        migrator.add_column_if_not_exists(
            ProtocolModel, ProtocolModel.started_at)
        migrator.add_column_if_not_exists(
            ProtocolModel, ProtocolModel.ended_at)
        migrator.add_column_if_not_exists(TaskModel, TaskModel.started_at)
        migrator.add_column_if_not_exists(TaskModel, TaskModel.ended_at)
        migrator.add_column_if_not_exists(
            ProgressBar, ProgressBar.current_value)
        migrator.add_column_if_not_exists(ProgressBar, ProgressBar.started_at)
        migrator.add_column_if_not_exists(ProgressBar, ProgressBar.ended_at)
        migrator.migrate()

        # refactor progress bar
        progress_bars: List[ProgressBar] = list(ProgressBar.select())
        for progress_bar in progress_bars:
            progress_bar_data: dict = progress_bar.data

            if 'messages' not in progress_bar_data or 'value' not in progress_bar_data:
                continue

            progress_bar.current_value = progress_bar_data['value']

            messages: List[dict] = progress_bar_data['messages']

            if len(messages) > 0:
                started_at: str = messages[0]['datetime']
                progress_bar.started_at = DateHelper.from_str(
                    started_at,  "%Y-%m-%dT%H:%M:%S.%f")

                ended_at: str = messages[-1]['datetime']
                progress_bar.ended_at = DateHelper.from_str(
                    ended_at,  "%Y-%m-%dT%H:%M:%S.%f")

            # keep only messages
            progress_bar.data = {'messages': progress_bar_data['messages']}
            progress_bar.save()

        process_models: List[ProcessModel] = list(
            TaskModel.select()) + list(ProtocolModel.select())
        for process_model in process_models:
            process_model.started_at = process_model.progress_bar.started_at
            process_model.ended_at = process_model.progress_bar.ended_at
            process_model.save()


@brick_migration('0.4.2', short_description='Add ram to monitor')
class Migration042(BrickMigration):

    @classmethod
    def migrate(cls, from_version: Version, to_version: Version) -> None:

        migrator: SqlMigrator = SqlMigrator(Monitor.get_db())
        migrator.add_column_if_not_exists(Monitor, Monitor.ram_usage_total)
        migrator.add_column_if_not_exists(Monitor, Monitor.ram_usage_used)
        migrator.add_column_if_not_exists(Monitor, Monitor.ram_usage_percent)
        migrator.add_column_if_not_exists(Monitor, Monitor.ram_usage_free)
        migrator.migrate()


@brick_migration('0.4.3', short_description='Add shared info and brick_version to ResourceModel. Update FileRField')
class Migration043(BrickMigration):

    @classmethod
    def migrate(cls, from_version: Version, to_version: Version) -> None:

        migrator: SqlMigrator = SqlMigrator(ResourceModel.get_db())
        migrator.add_column_if_not_exists(
            ResourceModel, ResourceModel.brick_version)
        migrator.migrate()

        # set brick_version
        resource_models: List[ResourceModel] = list(ResourceModel.select())
        for resource_model in resource_models:
            try:
                if resource_model.brick_version == '':
                    resource_model.set_resource_typing_name(
                        resource_model.resource_typing_name)

                # update all the FileRField to store only the name of the file instead of the full path
                resource: Resource = resource_model.get_resource()
                properties: Dict[str,
                                 BaseRField] = resource.__get_resource_r_fields__()

                for key, r_field in properties.items():
                    if isinstance(r_field, FileRField):
                        value = resource._kv_store.get(key)
                        # if this is a path, we store only the name of the file
                        if FileHelper.exists_on_os(value):
                            # unlock the kv_store to update it directly
                            resource._kv_store._lock = False
                            resource._kv_store[key] = FileHelper.get_name(
                                value)
                            resource._kv_store._lock = True

                resource_model.save()
            except Exception as exception:
                Logger.error(
                    f'Error while setting brick_version for {resource_model.resource_typing_name}, resource id {resource_model.id} : {exception}')


@brick_migration('0.4.4', short_description='Update config spec json')
class Migration044(BrickMigration):

    @classmethod
    def migrate(cls, from_version: Version, to_version: Version) -> None:

        # update config json
        configs: List[Config] = list(Config.select())
        for config in configs:
            specs = config.data['specs']

            changed = False
            new_specs = {}

            for key, spec in specs.items():
                # if the spec was already updated
                if 'additional_info' in spec:
                    continue

                new_specs[key] = cls.update_config_spec_json(spec)
                changed = True

            if changed:
                config.data['specs'] = new_specs
                config.save()

    @classmethod
    def update_config_spec_json(cls, config_spec_json: dict) -> dict:
        copy: dict = deepcopy(config_spec_json)

        specs = {}

        # copy all basic fields
        for key in ['type', 'optional', 'visibility', 'default_value',
                    'human_name', 'short_description', 'unit', 'allowed_values']:
            if key in copy:
                specs[key] = copy.get(key)
                del copy[key]

        # handle param set recursively
        if 'param_set' in copy:
            param_set = {}
            for key, spec in copy['param_set'].items():
                param_set[key] = cls.update_config_spec_json(spec)

            # replace the param set in the copy
            copy['param_set'] = param_set

        # add the rest json to additional_info
        specs['additional_info'] = copy

        return specs


@brick_migration('0.4.5', short_description='Clean progress bar messages and set process id to not null')
class Migration045(BrickMigration):

    @classmethod
    def migrate(cls, from_version: Version, to_version: Version) -> None:
        # clean progress bar messages
        ProgressBar.delete().where(ProgressBar.process_id is None).execute()
        ProgressBar.delete().where(ProgressBar.process_id == '').execute()

        migrator: SqlMigrator = SqlMigrator(ProgressBar.get_db())
        # set process_id and process_typing_name to not null
        migrator.alter_column_type(
            ProgressBar, 'process_id', CharField(null=False, index=True))
        migrator.alter_column_type(
            ProgressBar, 'process_typing_name', CharField(null=False))
        # remove old index
        migrator.drop_index_if_exists(
            ProgressBar, 'progressbar_process_id_process_typing_name')
        # create a unique index on process_id
        migrator.add_index_if_not_exists(
            ProgressBar, 'gws_process_progress_bar_process_id', ['process_id'], True)
        migrator.migrate()


@brick_migration('0.4.7', short_description='Remove created_by and last_modified_by from Project. Update kvstore path. Add external disk to monitor')
class Migration047(BrickMigration):
    """Remove created_by and last_modified_by from Project because project are synchronized on lab start

    :param BrickMigration: _description_
    :type BrickMigration: _type_
    """

    @classmethod
    def migrate(cls, from_version: Version, to_version: Version) -> None:

        migrator: SqlMigrator = SqlMigrator(Project.get_db())
        migrator.drop_column_if_exists(Project, "created_by_id")
        migrator.drop_column_if_exists(Project, "last_modified_by_id")
        migrator.add_column_if_not_exists(Monitor, Monitor.external_disk_total)
        migrator.add_column_if_not_exists(
            Monitor, Monitor.external_disk_usage_used)
        migrator.add_column_if_not_exists(
            Monitor, Monitor.external_disk_usage_free)
        migrator.add_column_if_not_exists(
            Monitor, Monitor.external_disk_usage_percent)
        migrator.migrate()

        # update kvstore path to an absolute clean path (replace /data/./kvstore by /data/kvstore)
        resources: List[ResourceModel] = list(ResourceModel.select())
        for resource in resources:
            try:
                if resource.kv_store_path is not None:
                    resource.kv_store_path = os.path.abspath(
                        resource.kv_store_path)
                    resource.save()
            except Exception as exception:
                Logger.error(
                    f'Error while updating kvstore path for {resource.resource_typing_name}, resource id {resource.id} : {exception}')


@brick_migration('0.5.0-beta.2', short_description='Update FsNode Rfield values')
class Migration050Beta1(BrickMigration):

    @classmethod
    def migrate(cls, from_version: Version, to_version: Version) -> None:

        resource_models: List[ResourceModel] = list(
            ResourceModel.get_by_types_and_sub([FSNode._typing_name]))

        for resource_model in resource_models:
            try:
                resource_model.data['path'] = resource_model.fs_node_model.path
                resource_model.data['file_store_id'] = resource_model.fs_node_model.file_store_id
                resource_model.save()
            except Exception as exception:
                Logger.error(
                    f'Error while setting brick_version for {resource_model.resource_typing_name}, resource id {resource_model.id} : {exception}')


@brick_migration('0.5.0-beta.5', short_description='Add photo to user', authenticate_sys_user=False)
class Migration050Beta5(BrickMigration):

    @classmethod
    def migrate(cls, from_version: Version, to_version: Version) -> None:

        migrator: SqlMigrator = SqlMigrator(User.get_db())
        migrator.add_column_if_not_exists(User, User.photo)
        migrator.migrate()


@brick_migration('0.5.0', short_description='Add project to resource')
class Migration050(BrickMigration):

    @classmethod
    def migrate(cls, from_version: Version, to_version: Version) -> None:

        migrator: SqlMigrator = SqlMigrator(ResourceModel.get_db())
        migrator.add_column_if_not_exists(ResourceModel, ResourceModel.project)
        migrator.migrate()

        resource_models: List[ResourceModel] = list(ResourceModel.select())

        for resource_model in resource_models:

            try:
                if resource_model.experiment and resource_model.experiment.project:
                    resource_model.project = resource_model.experiment.project
                    resource_model.save()
            except Exception as exception:
                Logger.error(
                    f'Error while setting project for resource id {resource_model.id} : {exception}')


@brick_migration('0.5.2', short_description='Add elapsed time and second start to progress bar')
class Migration052(BrickMigration):

    @classmethod
    def migrate(cls, from_version: Version, to_version: Version) -> None:

        migrator: SqlMigrator = SqlMigrator(ProgressBar.get_db())
        migrator.add_column_if_not_exists(
            ProgressBar, ProgressBar.elapsed_time)
        migrator.add_column_if_not_exists(
            ProgressBar, ProgressBar.second_start)
        migrator.migrate()

        progress_bars: List[ProgressBar] = list(ProgressBar.select())
        for progress_bar in progress_bars:
            try:
                if progress_bar.elapsed_time is None:
                    progress_bar.elapsed_time = progress_bar.get_elapsed_time()
                    progress_bar.save()
            except Exception as exception:
                Logger.error(
                    f'Error while setting elapsed time for progress bar id {progress_bar.id} : {exception}')


@brick_migration('0.5.5', short_description='Remove transformer from view config, add GPU to monitor')
class Migration055(BrickMigration):

    @classmethod
    def migrate(cls, from_version: Version, to_version: Version) -> None:

        migrator: SqlMigrator = SqlMigrator(ViewConfig.get_db())
        migrator.drop_column_if_exists(ViewConfig, "transformers")
        migrator.add_column_if_not_exists(Monitor, Monitor.gpu_percent)
        migrator.add_column_if_not_exists(Monitor, Monitor.gpu_temperature)
        migrator.add_column_if_not_exists(Monitor, Monitor.gpu_memory_total)
        migrator.add_column_if_not_exists(Monitor, Monitor.gpu_memory_free)
        migrator.add_column_if_not_exists(Monitor, Monitor.gpu_memory_used)
        migrator.add_column_if_not_exists(Monitor, Monitor.gpu_memory_percent)
        migrator.migrate()


@brick_migration('0.5.7', short_description='Clean activity table, refactor io_specs')
class Migration057(BrickMigration):

    @classmethod
    def migrate(cls, from_version: Version, to_version: Version) -> None:

        # remove all activities related to protocol model
        Activity.delete().where(
            (Activity.object_type == "gws_core.protocol.protocol_model.ProtocolModel") &
            (Activity.activity_type == "CREATE")).execute()

        Activity.update(object_type=ActivityObjectType.EXPERIMENT.value).where(
            Activity.object_type == "gws_core.experiment.experiment.Experiment").execute()

        Activity.update(object_type=ActivityType.VALIDATE.value).where(
            Activity.activity_type == "VALIDATE_EXPERIMENT").execute()

        Activity.update(activity_type=ActivityType.RUN_EXPERIMENT.value).where(
            Activity.activity_type == "START").execute()

        Activity.update(object_type=ActivityObjectType.USER.value).where(
            Activity.object_type.is_null()).execute()

        migrator: SqlMigrator = SqlMigrator(Activity.get_db())
        migrator.drop_index_if_exists(Activity, "activity_activity_type")
        migrator.drop_index_if_exists(Activity, "activity_object_type")
        migrator.drop_index_if_exists(Activity, "activity_object_id")
        migrator.alter_column_type(Activity, Activity.object_type.column_name,
                                   EnumField(choices=ActivityType, null=False))
        migrator.alter_column_type(
            Activity, Activity.object_id.column_name, CharField(null=False, max_length=36))
        migrator.migrate()

        # refactor io specs
        process_models: List[TaskModel] = list(TaskModel.select())
        for process_model in process_models:
            try:
                modified: bool = False
                inputs = process_model.data["inputs"]
                if not 'is_dynamic' in inputs and not 'ports' in inputs:
                    # wrap the current inputs in ports
                    process_model.data["inputs"] = {
                        "is_dynamic": False,
                        "ports": inputs
                    }
                    modified = True

                outputs = process_model.data["outputs"]
                if not 'is_dynamic' in outputs and not 'ports' in outputs:
                    # wrap the current outputs in ports
                    process_model.data["outputs"] = {
                        "is_dynamic": False,
                        "ports": outputs
                    }
                    modified = True

                if modified:
                    process_model.save(skip_hook=True)

            except Exception as exception:
                Logger.error(
                    f'Error while setting process type for process id {process_model.id} : {exception}')


class ReportResourceModel(PeeweeModel):
    class Meta:
        table_name = 'gws_report_resource'
        database = GwsCoreDbManager.get_db()


@brick_migration('0.6.0', short_description='Migrate tags, new table ReportViewModel')
class Migration060(BrickMigration):

    @classmethod
    def migrate(cls, from_version: Version, to_version: Version) -> None:

        migrator: SqlMigrator = SqlMigrator(ViewConfig.get_db())
        migrator.add_column_if_not_exists(TagKeyModel, TagKeyModel.value_format)
        migrator.add_column_if_not_exists(TagKeyModel, TagKeyModel.is_propagable)
        migrator.drop_column_if_exists(ViewConfig, 'config_values')
        migrator.alter_column_type(
            ViewConfig, ViewConfig.config.column_name,
            CharField(max_length=36, null=False, index=True))
        migrator.drop_table_if_exists(ReportResourceModel)
        migrator.migrate()

        TagKeyModel.update(value_format=EntityTagValueFormat.STRING).where(
            TagKeyModel.value_format.is_null()).execute()

        entities: List[TaggableModel] = list(
            ResourceModel.select()) + list(Experiment.select()) + list(ViewConfig.select())

        for entity in entities:
            try:
                tags = TagHelper.tags_to_list(entity.tags)

                for tag in tags:
                    entity_type: EntityType
                    if isinstance(entity, ResourceModel):
                        entity_type = EntityType.RESOURCE
                    elif isinstance(entity, Experiment):
                        entity_type = EntityType.EXPERIMENT
                    elif isinstance(entity, ViewConfig):
                        entity_type = EntityType.VIEW
                    entity_tag = EntityTag.find_by_tag_and_entity(tag, entity_type, entity.id)

                    if entity_tag is None:
                        tag.origins.add_origin(TagOriginType.USER, CurrentUserService.get_and_check_current_user().id)

                        tag_model = TagValueModel.create_tag_value_if_not_exists(tag.key, tag.value)
                        entity_tag = EntityTag.create_entity_tag(
                            tag=tag, value_format=tag_model.tag_key.value_format, entity_id=entity.id,
                            entity_type=entity_type)
            except Exception as exception:
                Logger.error(
                    f'Error while migrating tags for entity {type(entity).__name__} {entity.id} : {exception}')

        # fill ReportViewModel table
        report_models: List[Report] = list(Report.select())

        for report in report_models:
            try:
                rich_text = report.get_content_as_rich_text()

                report_updated = False

                for report_view in rich_text.get_resource_views_data():
                    if report_view.get('view_config_id') is None:
                        view_result = ResourceService.get_and_call_view_on_resource_model(report_view.get(
                            'resource_id'), report_view.get('view_method_name'), report_view.get('view_config'), True)

                        report_view['view_config_id'] = view_result.view_config.id
                        report_updated = True

                if report_updated:
                    report.content = rich_text.get_content()
                    report.save()
                    ReportService._refresh_report_views_and_tags(report)

            except Exception as exception:
                Logger.error(
                    f'Error while migrating report view for report {report.id} : {exception}')


class Comment(PeeweeModel):

    class Meta:
        table_name = "gws_comment"
        database = GwsCoreDbManager.get_db()


@brick_migration('0.6.2', short_description='Add level status in project, remove generic column data, archived and hash')
class Migration062(BrickMigration):

    @classmethod
    def migrate(cls, from_version: Version, to_version: Version) -> None:

        migrator: SqlMigrator = SqlMigrator(Project.get_db())
        # migrator.add_column_if_not_exists(Project, Project.level_status)
        migrator.add_column_if_not_exists(Project, EnumField(
            choices=ProjectLevelStatus, default=ProjectLevelStatus.LEAF), Project.level_status.column_name)
        # remove default
        migrator.alter_column_type(Project, Project.level_status.column_name, EnumField(
            choices=ProjectLevelStatus, max_length=20))

        migrator.drop_table_if_exists(Comment)
        migrator.drop_table_if_exists(ReportResourceModel)
        migrator.migrate()

        # remove generic column data, archived and hash
        models: List[Type[Model]] = Model.inheritors()
        # list of models to exclude (that use data column)
        exclude_data = [
            BrickModel.get_table_name(),
            Config.get_table_name(),
            Credentials.get_table_name(),
            Experiment.get_table_name(),
            FileStore.get_table_name(),
            Monitor.get_table_name(),
            Typing.get_table_name(),
            TaskModel.get_table_name(),
            ProtocolModel.get_table_name(),
            ProgressBar.get_table_name(),
            ProtocolTemplate.get_table_name(),
            ResourceModel.get_table_name()]
        exclude_archive = [Experiment.get_table_name(), TaskModel.get_table_name(), ProtocolModel.get_table_name(),
                           Report.get_table_name(), ResourceModel.get_table_name()]
        migrator = SqlMigrator(Model.get_db())

        for model in models:
            if not model.get_table_name() or not model.get_table_name().startswith('gws') or model.get_table_name().startswith('biota'):
                continue

            if model.get_table_name() not in exclude_data:
                try:
                    migrator.drop_column_if_exists(model, 'data')
                except Exception as exception:
                    Logger.error(
                        f'Error while removing data column for model {model.__name__} : {exception}')

            if model.get_table_name() not in exclude_archive:
                try:
                    migrator.drop_column_if_exists(model, 'is_archived')
                except Exception as exception:
                    Logger.error(
                        f'Error while removing archived column for model {model.__name__} : {exception}')

            try:
                migrator.drop_column_if_exists(model, 'hash')
            except Exception as exception:
                Logger.error(
                    f'Error while removing hash column for model {model.__name__} : {exception}')

        migrator.migrate()


@brick_migration('0.7.3', short_description='Rename view config flagged to favorite and add run_brick_version to process_model. Simplify resource origin')
class Migration073(BrickMigration):

    @classmethod
    def migrate(cls, from_version: Version, to_version: Version) -> None:

        migrator: SqlMigrator = SqlMigrator(ViewConfig.get_db())
        migrator.rename_column_if_exists(ViewConfig, 'flagged', 'is_favorite')
        migrator.rename_column_if_exists(TaskModel, 'brick_version', 'brick_version_on_create')
        migrator.rename_column_if_exists(ProtocolModel, 'brick_version', 'brick_version_on_create')
        migrator.add_column_if_not_exists(TaskModel, TaskModel.brick_version_on_run)
        migrator.add_column_if_not_exists(ProtocolModel, ProtocolModel.brick_version_on_run)
        migrator.add_column_if_not_exists(Experiment, Experiment.creation_type)
        migrator.migrate()

        process_models: List[ProcessModel] = list(TaskModel.select()) + list(ProtocolModel.select())
        for process_model in process_models:
            if not process_model.brick_version_on_run:
                process_model.brick_version_on_run = process_model.brick_version_on_create
                process_model.save(skip_hook=True)

        ResourceModel.update(origin=ResourceOrigin.GENERATED).where(
            ResourceModel.origin.in_(["IMPORTED", "EXPORTED", "TRANSFORMED", "ACTIONS"])).execute()

        if Experiment.column_exists('type'):
            Experiment.get_db().execute_sql('UPDATE gws_experiment SET creation_type = "MANUAL" WHERE type = "EXPERIMENT"')
            Experiment.get_db().execute_sql('UPDATE gws_experiment SET creation_type = "AUTO" WHERE type in ("TRANSFORMER", "IMPORTER", "EXPORTER", "FS_NODE_EXTRACTOR", "RESOURCE_DOWNLOADER", "ACTIONS")')
            migrator = SqlMigrator(Experiment.get_db())
            migrator.drop_column_if_exists(Experiment, 'type')
            migrator.migrate()


@brick_migration('0.7.5', short_description='Add name to process model. Migrate protocol IOFaces. Add community live task version id column to Task model')
class Migration075(BrickMigration):

    @classmethod
    def migrate(cls, from_version: Version, to_version: Version) -> None:

        migrator: SqlMigrator = SqlMigrator(TaskModel.get_db())
        migrator.add_column_if_not_exists(TaskModel, TaskModel.name)
        migrator.add_column_if_not_exists(TaskModel, TaskModel.community_live_task_version_id)
        migrator.add_column_if_not_exists(ProtocolModel, ProtocolModel.name)
        migrator.migrate()

        process_models: List[ProcessModel] = list(TaskModel.select()) + list(ProtocolModel.select())
        for process_model in process_models:
            if not process_model.name:
                process_type = TypingManager.get_typing_from_name(process_model.process_typing_name)
                if process_type:
                    process_model.name = process_type.human_name
                else:
                    process_model.name = process_model.instance_name
                process_model.save(skip_hook=True)

        # migrate protocol template to new name
        protocol_templates: List[ProtocolTemplate] = list(ProtocolTemplate.select())
        for protocol_template in protocol_templates:
            cls.migrate_protocol_template_recur(protocol_template.data)
            protocol_template.save(skip_hook=True)

        # simplify the json stored for interface and outerface
        protocol_models: List[ProtocolModel] = list(ProtocolModel.select())
        for protocol_model in protocol_models:
            cls.migrate_protocol_iofaces(protocol_model.data["graph"])
            protocol_model.save(skip_hook=True)

        # fix old activity type
        Activity.update(activity_type=ActivityType.STOP_EXPERIMENT.value).where(
            Activity.activity_type == "STOP").execute()

    @classmethod
    def migrate_protocol_template_recur(cls, protocol_graph: dict) -> None:
        for process_dto in protocol_graph["nodes"].values():
            if "name" not in process_dto:
                process_dto["name"] = process_dto["human_name"]

            if "process_type" not in process_dto:
                process_dto["process_type"] = {
                    "human_name": process_dto["human_name"],
                    "short_description": process_dto["short_description"]
                }

            if "human_name" in process_dto:
                del process_dto["human_name"]
            if "short_description" in process_dto:
                del process_dto["short_description"]

            if process_dto.get('graph') is not None and "nodes" in process_dto["graph"]:
                cls.migrate_protocol_template_recur(process_dto["graph"])
        cls.migrate_protocol_iofaces(protocol_graph)

    @classmethod
    def migrate_protocol_iofaces(cls, protocol_graph: dict) -> None:
        for interface in protocol_graph["interfaces"].values():
            if "to" in interface:
                interface["process_instance_name"] = interface["to"]["node"]
                interface["port_name"] = interface["to"]["port"]
                del interface["to"]
            if "from" in interface:
                del interface["from"]

        for outerface in protocol_graph["outerfaces"].values():
            if "from" in outerface:
                outerface["process_instance_name"] = outerface["from"]["node"]
                outerface["port_name"] = outerface["from"]["port"]
                del outerface["from"]
            if "to" in outerface:
                del outerface["to"]


@brick_migration('0.8.0-beta.1', short_description='Remove old rich text. Add style to entities.')
class Migration080Beta1(BrickMigration):

    @classmethod
    def migrate(cls, from_version: Version, to_version: Version) -> None:

        migrator: SqlMigrator = SqlMigrator(Report.get_db())
        migrator.drop_column_if_exists(Report, 'old_content')
        migrator.drop_column_if_exists(ReportTemplate, "old_content")
        migrator.drop_column_if_exists(Experiment, "old_description")
        migrator.drop_column_if_exists(ProtocolTemplate, "old_description")
        migrator.drop_column_if_exists(Typing, "icon")
        migrator.add_column_if_not_exists(Typing, Typing.style)
        migrator.add_column_if_not_exists(ViewConfig, ViewConfig.style)
        migrator.add_column_if_not_exists(ResourceModel, ResourceModel.style)
        migrator.add_column_if_not_exists(TaskModel, TaskModel.style)
        migrator.add_column_if_not_exists(ProtocolModel, ProtocolModel.style)

        migrator.migrate()

        protocol_templates: List[ProtocolTemplate] = list(ProtocolTemplate.select())
        for protocol_template in protocol_templates:
            cls.migrate_template_data(protocol_template.data)
            protocol_template.save(skip_hook=True)

    @classmethod
    def migrate_template_data(cls, graph: dict) -> None:
        for node in graph["nodes"].values():
            if "style" not in node:
                node["style"] = TypingStyle.default_task().to_json_dict()

            if node.get('graph'):
                cls.migrate_template_data(node["graph"])


@brick_migration('0.8.0', short_description='Delete virtual environments for new format')
class Migration080(BrickMigration):

    @classmethod
    def migrate(cls, from_version: Version, to_version: Version) -> None:

        migrator: SqlMigrator = SqlMigrator(Experiment.get_db())
        migrator.drop_column_if_exists(Experiment, 'score')
        migrator.add_column_if_not_exists(ResourceModel, ResourceModel.content_is_deleted)

        migrator.migrate()

        # delete all virtual environments
        VEnvService.delete_all_venvs()
