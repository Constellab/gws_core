

import os
from copy import deepcopy
from typing import Dict, List

from peewee import BigIntegerField, CharField

from gws_core.brick.brick_helper import BrickHelper
from gws_core.config.config import Config
from gws_core.core.classes.enum_field import EnumField
from gws_core.core.db.sql_migrator import SqlMigrator
from gws_core.core.utils.date_helper import DateHelper
from gws_core.folder.space_folder import SpaceFolder
from gws_core.impl.file.file_helper import FileHelper
from gws_core.impl.file.file_r_field import FileRField
from gws_core.impl.file.fs_node import FSNode
from gws_core.impl.file.fs_node_model import FSNodeModel
from gws_core.impl.rich_text.rich_text import RichText
from gws_core.impl.rich_text.rich_text_file_service import RichTextFileService
from gws_core.impl.rich_text.rich_text_types import (RichTextDTO,
                                                     RichTextObjectType)
from gws_core.impl.shell.virtual_env.venv_service import VEnvService
from gws_core.lab.lab_config_model import LabConfigModel
from gws_core.lab.monitor.monitor import Monitor
from gws_core.model.typing import Typing
from gws_core.model.typing_manager import TypingManager
from gws_core.model.typing_style import TypingStyle
from gws_core.note.note import Note, NoteScenario
from gws_core.note.note_view_model import NoteViewModel
from gws_core.note_template.note_template import NoteTemplate
from gws_core.process.process_model import ProcessModel
from gws_core.progress_bar.progress_bar import ProgressBar
from gws_core.protocol.protocol_model import ProtocolModel
from gws_core.resource.r_field.r_field import BaseRField
from gws_core.resource.resource import Resource
from gws_core.resource.resource_dto import ResourceOrigin
from gws_core.resource.resource_model import ResourceModel
from gws_core.resource.resource_set.resource_list_base import ResourceListBase
from gws_core.resource.resource_set.resource_set import ResourceSet
from gws_core.resource.view_config.view_config import ViewConfig
from gws_core.scenario.queue import Job
from gws_core.scenario.scenario import Scenario
from gws_core.scenario_template.scenario_template import ScenarioTemplate
from gws_core.scenario_template.scenario_template_factory import \
    ScenarioTemplateFactory
from gws_core.share.shared_scenario import SharedScenario
from gws_core.tag.entity_tag import EntityTag
from gws_core.tag.tag_key_model import TagKeyModel
from gws_core.tag.tag_value_model import TagValueModel
from gws_core.task.plug import Sink, Source
from gws_core.task.task_input_model import TaskInputModel
from gws_core.task.task_model import TaskModel
from gws_core.user.activity.activity import Activity
from gws_core.user.activity.activity_dto import (ActivityObjectType,
                                                 ActivityType)
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


@brick_migration('0.2.3', short_description='Create LabConfigModel table and add lab_config_id to scenario')
class Migration023(BrickMigration):

    @classmethod
    def migrate(cls, from_version: Version, to_version: Version) -> None:
        LabConfigModel.create_table()

        migrator: SqlMigrator = SqlMigrator(Scenario.get_db())

        migrator.add_column_if_not_exists(Scenario, Scenario.lab_config)
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


@brick_migration('0.3.8', short_description='Create lab config column in note table')
class Migration038(BrickMigration):

    @classmethod
    def migrate(cls, from_version: Version, to_version: Version) -> None:

        migrator: SqlMigrator = SqlMigrator(Note.get_db())

        migrator.add_column_if_not_exists(Note, Note.lab_config)
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
                    output_resources[port_name] = port.get_resource_model()

                input_resources: Dict[str, ResourceModel] = {}
                for port_name, port in process_model.inputs.ports.items():
                    input_resources[port_name] = port.get_resource_model()

                # update io specs
                process_model.set_process_type(process_model.get_process_type())

                # set port output from output_resources
                for port_name, port in process_model.outputs.ports.items():
                    if port_name in output_resources:
                        port.set_resource_model(output_resources[port_name])
                process_model.data["outputs"] = process_model.outputs.to_dto().to_json_dict()

                # set port input from input_resources
                for port_name, port in process_model.inputs.ports.items():
                    if port_name in input_resources:
                        port.set_resource_model(input_resources[port_name])

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
            TaskModel.process_typing_name == Source.get_typing_name()))

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
                children_resources = resource_set.get_resource_models()
                for child_resource_model in children_resources:
                    # update the parent only if the resource was created by the same task than parent (meaning it was created with the resource set)
                    if resource_model.task_model == child_resource_model.task_model:
                        child_resource_model.parent_resource_id = resource_model
                        child_resource_model.save()
            except Exception as err:
                Logger.error(
                    f'Error while migrating resource {resource_model.id} : {err}')
                Logger.log_exception_stack_trace(err)


@brick_migration('0.3.13', short_description='Update orgin values of resources, add show_in_databox and generated_by_port_name columns. Add validated info to scenario and note')
class Migration0313(BrickMigration):

    @classmethod
    def migrate(cls, from_version: Version, to_version: Version) -> None:

        migrator: SqlMigrator = SqlMigrator(ResourceModel.get_db())

        migrator.add_column_if_not_exists(ResourceModel, ResourceModel.flagged)
        migrator.add_column_if_not_exists(
            ResourceModel, ResourceModel.generated_by_port_name)
        migrator.add_column_if_not_exists(Scenario, Scenario.validated_at)
        migrator.add_column_if_not_exists(Scenario, Scenario.validated_by)
        migrator.add_column_if_not_exists(Note, Note.validated_at)
        migrator.add_column_if_not_exists(Note, Note.validated_by)
        migrator.migrate()

        # retrieve all resource of type  ResourceListBase or children
        resource_models: List[ResourceModel] = list(ResourceModel.select())
        for resource_model in resource_models:

            try:
                # update orgin values
                # if resource_model.scenario is not None:
                #     if resource_model.scenario.type == ScenarioType.IMPORTER:
                #         resource_model.origin = ResourceOrigin.GENERATED
                #     elif resource_model.scenario.type == ScenarioType.TRANSFORMER:
                #         resource_model.origin = ResourceOrigin.GENERATED

                # set show_in_databox
                task_input_model: TaskInputModel = TaskInputModel.get_by_resource_model(
                    resource_model.id).first()
                # if the resource is used a input of a Sink task or the resource was uploaded
                if (task_input_model is not None and task_input_model.task_model.process_typing_name == Sink.get_typing_name()) or \
                        resource_model.origin == ResourceOrigin.UPLOADED:
                    resource_model.flagged = True

                # set generated by port name
                if resource_model.task_model is not None:
                    # If this is a child resource, take the parent id as generated by port name
                    resource_model_id = resource_model.id if resource_model.parent_resource_id is None else resource_model.parent_resource_id
                    # loop thourgh task output and check if the resource correspond to the resource in the port
                    for port_name, port in resource_model.task_model.outputs.ports.items():
                        if port.get_resource_model() and port.get_resource_model_id() == resource_model_id:
                            resource_model.generated_by_port_name = port_name
                            break

                resource_model.save()

            except Exception as err:
                Logger.error(
                    f'Error while migrating resource {resource_model.id} : {err}')
                Logger.log_exception_stack_trace(err)

        # update validated info to scenario and note
        scenario_models: List[Scenario] = list(Scenario.select())
        for scenario_model in scenario_models:
            if scenario_model.is_validated:
                scenario_model.validated_at = scenario_model.last_modified_at
                scenario_model.validated_by = scenario_model.last_modified_by
                scenario_model.save()

        note_models: List[Note] = list(Note.select())
        for note_model in note_models:
            if note_model.is_validated:
                note_model.validated_at = note_model.last_modified_at
                note_model.validated_by = note_model.last_modified_by
                note_model.save()


@brick_migration('0.3.14', short_description='Update table meta (tags)')
class Migration0314(BrickMigration):
    @classmethod
    def migrate(cls, from_version: Version, to_version: Version) -> None:
        pass
        # migration deprecated, tags are now stored in the resource model


@brick_migration('0.3.15', short_description='Add last_sync info to Scenario and Note')
class Migration0315(BrickMigration):

    @classmethod
    def migrate(cls, from_version: Version, to_version: Version) -> None:

        migrator: SqlMigrator = SqlMigrator(Scenario.get_db())
        migrator.add_column_if_not_exists(Scenario, Scenario.last_sync_at)
        migrator.add_column_if_not_exists(Scenario, Scenario.last_sync_by)
        migrator.add_column_if_not_exists(Note, Note.last_sync_at)
        migrator.add_column_if_not_exists(Note, Note.last_sync_by)
        migrator.migrate()

        scenarios: List[Scenario] = list(
            Scenario.select().where(Scenario.is_validated == True))
        for scenario in scenarios:
            scenario.last_sync_at = scenario.last_modified_at
            scenario.last_sync_by = scenario.last_modified_by
            scenario.save()

        notes: List[Note] = list(
            Note.select().where(Note.is_validated == True))
        for note in notes:
            note.last_sync_at = note.last_modified_at
            note.last_sync_by = note.last_modified_by
            note.save()


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
            Scenario, Scenario.tags.column_name, CharField(null=True, max_length=255))
        migrator.alter_column_type(
            ResourceModel, ResourceModel.tags.column_name, CharField(null=True, max_length=255))
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
                        value = resource.__kv_store__.get(key)
                        # if this is a path, we store only the name of the file
                        if FileHelper.exists_on_os(value):
                            # unlock the kv_store to update it directly
                            resource.__kv_store__._lock = False
                            resource.__kv_store__[key] = FileHelper.get_name(
                                value)
                            resource.__kv_store__._lock = True

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


@brick_migration('0.5.0-beta.2', short_description='Update FsNode Rfield values')
class Migration050Beta1(BrickMigration):

    @classmethod
    def migrate(cls, from_version: Version, to_version: Version) -> None:

        resource_models: List[ResourceModel] = list(
            ResourceModel.get_by_types_and_sub([FSNode.get_typing_name()]))

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
        migrator.add_column_if_not_exists(ResourceModel, ResourceModel.folder)
        migrator.migrate()

        resource_models: List[ResourceModel] = list(ResourceModel.select())

        for resource_model in resource_models:

            try:
                if resource_model.scenario and resource_model.scenario.folder:
                    resource_model.folder = resource_model.scenario.folder
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

        Activity.update(object_type=ActivityObjectType.SCENARIO.value).where(
            Activity.object_type == "gws_core.scenario.scenario.Scenario").execute()

        Activity.update(object_type=ActivityType.VALIDATE.value).where(
            Activity.activity_type == "VALIDATE_SCENARIO").execute()

        Activity.update(activity_type=ActivityType.RUN_SCENARIO.value).where(
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
        migrator.add_column_if_not_exists(Scenario, Scenario.creation_type)
        migrator.migrate()

        process_models: List[ProcessModel] = list(TaskModel.select()) + list(ProtocolModel.select())
        for process_model in process_models:
            if not process_model.brick_version_on_run:
                process_model.brick_version_on_run = process_model.brick_version_on_create
                process_model.save(skip_hook=True)

        ResourceModel.update(origin=ResourceOrigin.GENERATED).where(
            ResourceModel.origin.in_(["IMPORTED", "EXPORTED", "TRANSFORMED", "ACTIONS"])).execute()

        if Scenario.column_exists('type'):
            Scenario.get_db().execute_sql('UPDATE gws_scenario SET creation_type = "MANUAL" WHERE type = "SCENARIO"')
            Scenario.get_db().execute_sql('UPDATE gws_scenario SET creation_type = "AUTO" WHERE type in ("TRANSFORMER", "IMPORTER", "EXPORTER", "FS_NODE_EXTRACTOR", "RESOURCE_DOWNLOADER", "ACTIONS")')
            migrator = SqlMigrator(Scenario.get_db())
            migrator.drop_column_if_exists(Scenario, 'type')
            migrator.migrate()


@brick_migration('0.7.5', short_description='Add name to process model. Migrate protocol IOFaces. Add community agent version id column to Task model')
class Migration075(BrickMigration):

    @classmethod
    def migrate(cls, from_version: Version, to_version: Version) -> None:

        migrator: SqlMigrator = SqlMigrator(TaskModel.get_db())
        migrator.add_column_if_not_exists(TaskModel, TaskModel.name)
        migrator.add_column_if_not_exists(TaskModel, TaskModel.community_agent_version_id)
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

        # migrate scenario template to new name
        scenario_templates: List[ScenarioTemplate] = list(ScenarioTemplate.select())
        for scenario_template in scenario_templates:
            cls.migrate_scenario_template_recur(scenario_template.data)
            scenario_template.save(skip_hook=True)

        # simplify the json stored for interface and outerface
        protocol_models: List[ProtocolModel] = list(ProtocolModel.select())
        for protocol_model in protocol_models:
            cls.migrate_protocol_iofaces(protocol_model.data["graph"])
            protocol_model.save(skip_hook=True)

        # fix old activity type
        Activity.update(activity_type=ActivityType.STOP_SCENARIO.value).where(
            Activity.activity_type == "STOP").execute()

    @classmethod
    def migrate_scenario_template_recur(cls, protocol_graph: dict) -> None:
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
                cls.migrate_scenario_template_recur(process_dto["graph"])
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

        migrator: SqlMigrator = SqlMigrator(Note.get_db())
        migrator.drop_column_if_exists(Note, 'old_content')
        migrator.drop_column_if_exists(NoteTemplate, "old_content")
        migrator.drop_column_if_exists(Scenario, "old_description")
        migrator.drop_column_if_exists(ScenarioTemplate, "old_description")
        migrator.drop_column_if_exists(Typing, "icon")
        migrator.add_column_if_not_exists(Typing, Typing.style)
        migrator.add_column_if_not_exists(ViewConfig, ViewConfig.style)
        migrator.add_column_if_not_exists(ResourceModel, ResourceModel.style)
        migrator.add_column_if_not_exists(TaskModel, TaskModel.style)
        migrator.add_column_if_not_exists(ProtocolModel, ProtocolModel.style)

        migrator.migrate()

        scenario_templates: List[ScenarioTemplate] = list(ScenarioTemplate.select())
        for scenario_template in scenario_templates:
            cls.migrate_template_data(scenario_template.data)
            scenario_template.save(skip_hook=True)

    @classmethod
    def migrate_template_data(cls, graph: dict) -> None:
        for node in graph["nodes"].values():
            if "style" not in node:
                node["style"] = TypingStyle.default_task().to_json_dict()

            if node.get('graph'):
                cls.migrate_template_data(node["graph"])


@brick_migration('0.8.0', short_description='Delete virtual environments for new format. Remove external disk usage from monitor. Remove old tags columns.')
class Migration080(BrickMigration):

    @classmethod
    def migrate(cls, from_version: Version, to_version: Version) -> None:

        migrator: SqlMigrator = SqlMigrator(Scenario.get_db())
        migrator.drop_column_if_exists(Scenario, 'score')

        migrator.drop_column_if_exists(Monitor, 'external_disk_total')
        migrator.drop_column_if_exists(Monitor, 'external_disk_usage_used')
        migrator.drop_column_if_exists(Monitor, 'external_disk_usage_percent')
        migrator.drop_column_if_exists(Monitor, 'external_disk_usage_free')

        migrator.drop_column_if_exists(Scenario, 'tags')
        migrator.drop_column_if_exists(ScenarioTemplate, 'tags')
        migrator.drop_column_if_exists(ResourceModel, 'tags')
        migrator.drop_column_if_exists(ViewConfig, 'tags')

        migrator.add_column_if_not_exists(ResourceModel, ResourceModel.content_is_deleted)
        migrator.alter_column_type(SpaceFolder, SpaceFolder.title.column_name, CharField(null=False, max_length=100))

        migrator.migrate()

        # delete all virtual environments
        VEnvService.delete_all_venvs()


@brick_migration('0.8.4', short_description='Rename note template to document table. Migrate template protocol. Migrate note image')
class Migration084(BrickMigration):

    @classmethod
    def migrate(cls, from_version: Version, to_version: Version) -> None:

        migrator: SqlMigrator = SqlMigrator(NoteTemplate.get_db())

        migrator.rename_table_if_exists(NoteTemplate, "gws_note_template")
        migrator.migrate()

        scenario_templates: List[ScenarioTemplate] = list(
            ScenarioTemplate.select().where(ScenarioTemplate.version == 1))

        for scenario_template in scenario_templates:
            scenario_template.data = ScenarioTemplateFactory.migrate_data_from_1_to_3(scenario_template.data)
            scenario_template.version = 3
            scenario_template.save(skip_hook=True)

        # migrate note images
        notes: List[Note] = list(Note.select())
        for note in notes:
            cls._migrate_rich_text_image(note.content, RichTextObjectType.NOTE, note.id)

        # migrate document images
        note_templates: List[NoteTemplate] = list(NoteTemplate.select())
        for note_template in note_templates:
            cls._migrate_rich_text_image(note_template.content,
                                         RichTextObjectType.NOTE_TEMPLATE, note_template.id)

    @classmethod
    def _migrate_rich_text_image(
            cls, rich_text_dto: RichTextDTO, object_type: RichTextObjectType, object_id: str) -> None:

        rich_text = RichText(rich_text_dto)
        for figure in rich_text.get_figures_data():
            new_dir = RichTextFileService.get_object_dir_path(object_type, object_id)

            FileHelper.create_dir_if_not_exist(new_dir)
            new_path = os.path.join(new_dir, figure['filename'])
            old_path = os.path.join(RichTextFileService._get_dir_path(), figure['filename'])

            if FileHelper.exists_on_os(old_path) and not FileHelper.exists_on_os(new_path):
                FileHelper.copy_file(old_path, new_path)


@brick_migration('0.10.0', short_description='Rename project to folder.')
class Migration0100(BrickMigration):

    @classmethod
    def migrate(cls, from_version: Version, to_version: Version) -> None:

        migrator: SqlMigrator = SqlMigrator(ResourceModel.get_db())
        migrator.rename_table_if_exists(SpaceFolder, 'gws_project')
        migrator.rename_table_if_exists(Note, 'gws_report')
        migrator.rename_table_if_exists(NoteScenario, 'gws_report_experiment')
        migrator.rename_table_if_exists(NoteViewModel, 'gws_report_view')
        migrator.rename_table_if_exists(Scenario, 'gws_experiment')
        migrator.rename_table_if_exists(SharedScenario, 'gws_shared_experiment')
        migrator.rename_table_if_exists(NoteTemplate, 'gws_document_template')
        migrator.rename_table_if_exists(ScenarioTemplate, 'gws_protocol_template')
        migrator.migrate()

        migrator_2: SqlMigrator = SqlMigrator(ResourceModel.get_db())
        migrator_2.drop_column_if_exists(SpaceFolder, 'level_status')
        migrator_2.drop_column_if_exists(SpaceFolder, 'code')
        # rename all project id
        migrator_2.rename_column_if_exists(Note, 'project_id', 'folder_id')
        migrator_2.rename_column_if_exists(Scenario, 'project_id', 'folder_id')
        migrator_2.rename_column_if_exists(ResourceModel, 'project_id', 'folder_id')
        # rename all scenario_id
        migrator_2.rename_column_if_exists(ProtocolModel, 'experiment_id', 'scenario_id')
        migrator_2.rename_column_if_exists(TaskModel, 'experiment_id', 'scenario_id')
        migrator_2.rename_column_if_exists(Job, 'experiment_id', 'scenario_id')
        migrator_2.rename_column_if_exists(ResourceModel, 'experiment_id', 'scenario_id')
        migrator_2.rename_column_if_exists(TaskInputModel, 'experiment_id', 'scenario_id')
        migrator_2.rename_column_if_exists(ViewConfig, 'experiment_id', 'scenario_id')
        migrator_2.rename_column_if_exists(TaskModel, 'community_live_task_version_id', 'community_agent_version_id')
        migrator_2.migrate()

        # use manual query, rename column doesn't work for primary key
        if NoteScenario.column_exists('report_id'):
            NoteScenario.get_db().execute_sql('ALTER TABLE gws_note_scenario CHANGE report_id note_id VARCHAR(36) NOT NULL')

        if NoteViewModel.column_exists('report_id'):
            NoteViewModel.get_db().execute_sql('ALTER TABLE gws_note_view CHANGE report_id note_id VARCHAR(36) NOT NULL')

        if NoteScenario.column_exists('experiment_id'):
            NoteScenario.get_db().execute_sql('ALTER TABLE gws_note_scenario CHANGE experiment_id scenario_id VARCHAR(36) NOT NULL')

        ResourceModel.update(origin=ResourceOrigin.S3_FOLDER_STORAGE).where(
            ResourceModel.origin == "S3_PROJECT_STORAGE").execute()

        TagValueModel.update(tag_value='data-hub-storage').where(
            TagValueModel.tag_value == "projects-storage").execute()

        Activity.update(object_type=ActivityObjectType.NOTE.value).where(
            Activity.object_type == "NOTE").execute()

        # rename document_template_param to note_template_param
        Config.get_db().execute_sql("UPDATE gws_config SET data = REPLACE(data, 'document_template_param', 'note_template_param')")
        Config.get_db().execute_sql("UPDATE gws_task SET data = REPLACE(data, 'DocumentTemplateResource', 'NoteTemplateResource')")

        # rename report to note in objects
        Config.get_db().execute_sql("UPDATE gws_config SET data = REPLACE(data, 'report_param', 'note_param')")

        resource_renames = {
            'RESOURCE.gws_core.ReportResource': 'RESOURCE.gws_core.NoteResource',
            'RESOURCE.gws_core.ENoteResource': 'RESOURCE.gws_core.NoteResource',
            'RESOURCE.gws_core.DocumentTemplateResource': 'RESOURCE.gws_core.NoteTemplateResource',
        }

        for old_typing_name, new_typing_name in resource_renames.items():
            SqlMigrator.rename_resource_typing_name(ResourceModel.get_db(), old_typing_name, new_typing_name)

        # rename live tasks to agents
        agent_renames = {
            'TASK.gws_core.PyLiveTask': 'TASK.gws_core.PyAgent',
            'TASK.gws_core.PyCondaLiveTask': 'TASK.gws_core.PyCondaAgent',
            'TASK.gws_core.PyMambaLiveTask': 'TASK.gws_core.PyMambaAgent',
            'TASK.gws_core.PyPipenvLiveTask': 'TASK.gws_core.PyPipenvAgent',
            'TASK.gws_core.RCondaLiveTask': 'TASK.gws_core.RCondaAgent',
            'TASK.gws_core.RMambaLiveTask': 'TASK.gws_core.RMambaAgent',
            'TASK.gws_core.StreamlitLiveTask': 'TASK.gws_core.StreamlitAgent',
        }

        for old_typing_name, new_typing_name in agent_renames.items():
            SqlMigrator.rename_process_typing_name(ResourceModel.get_db(), old_typing_name, new_typing_name)

    @brick_migration('0.10.1', short_description='Migrate tags and user activity')
    class Migration0101(BrickMigration):

        @classmethod
        def migrate(cls, from_version: Version, to_version: Version) -> None:
            EntityTag.get_db().execute_sql("UPDATE gws_entity_tag SET entity_type = 'SCENARIO' WHERE entity_type = 'EXPERIMENT'")
            EntityTag.get_db().execute_sql("UPDATE gws_entity_tag SET entity_type = 'NOTE' WHERE entity_type = 'REPORT'")
            EntityTag.get_db().execute_sql("UPDATE gws_entity_tag SET origins = REPLACE(origins, 'EXPERIMENT_PROPAGATED', 'SCENARIO_PROPAGATED')")
            Activity.get_db().execute_sql("UPDATE gws_user_activity SET activity_type = 'RUN_SCENARIO' where activity_type = 'RUN_EXPERIMENT'")
            Activity.get_db().execute_sql("UPDATE gws_user_activity SET activity_type = 'DELETE_SCENARIO_INTERMEDIATE_RESOURCES' where activity_type = 'DELETE_EXPERIMENT_INTERMEDIATE_RESOURCES'")
            Activity.get_db().execute_sql("UPDATE gws_user_activity SET activity_type = 'STOP_SCENARIO' where activity_type = 'STOP_EXPERIMENT'")
            Activity.get_db().execute_sql("UPDATE gws_user_activity SET object_type = 'SCENARIO' where object_type = 'EXPERIMENT'")
            Activity.get_db().execute_sql("UPDATE gws_user_activity SET object_type = 'NOTE_TEMPLATE' where object_type = 'DOCUMENT_TEMPLATE'")
            Activity.get_db().execute_sql("UPDATE gws_user_activity SET object_type = 'NOTE' where object_type = 'REPORT'")

    @brick_migration('0.10.2', short_description='Migrate share link')
    class Migration0102(BrickMigration):

        @classmethod
        def migrate(cls, from_version: Version, to_version: Version) -> None:
            EntityTag.get_db().execute_sql("UPDATE gws_share_link SET entity_type = 'SCENARIO' WHERE entity_type = 'EXPERIMENT'")

            # rename resource and agent in scenario template
            resource_renames = {
                'RESOURCE.gws_core.ReportResource': 'RESOURCE.gws_core.NoteResource',
                'RESOURCE.gws_core.ENoteResource': 'RESOURCE.gws_core.NoteResource',
                'RESOURCE.gws_core.DocumentTemplateResource': 'RESOURCE.gws_core.NoteTemplateResource',
            }

            for old_typing_name, new_typing_name in resource_renames.items():
                SqlMigrator.rename_resource_typing_name(ResourceModel.get_db(), old_typing_name, new_typing_name)

            agent_renames = {
                'TASK.gws_core.PyLiveTask': 'TASK.gws_core.PyAgent',
                'TASK.gws_core.PyCondaLiveTask': 'TASK.gws_core.PyCondaAgent',
                'TASK.gws_core.PyMambaLiveTask': 'TASK.gws_core.PyMambaAgent',
                'TASK.gws_core.PyPipenvLiveTask': 'TASK.gws_core.PyPipenvAgent',
                'TASK.gws_core.RCondaLiveTask': 'TASK.gws_core.RCondaAgent',
                'TASK.gws_core.RMambaLiveTask': 'TASK.gws_core.RMambaAgent',
                'TASK.gws_core.StreamlitLiveTask': 'TASK.gws_core.StreamlitAgent',
            }

            for old_typing_name, new_typing_name in agent_renames.items():
                SqlMigrator.rename_process_typing_name(ResourceModel.get_db(), old_typing_name, new_typing_name)

    @brick_migration('0.10.3', short_description='Migrate note and note template images')
    class Migration0103(BrickMigration):

        @classmethod
        def migrate(cls, from_version: Version, to_version: Version) -> None:
            FileHelper.create_dir_if_not_exist('/data/note')
            FileHelper.create_dir_if_not_exist('/data/note/note')
            FileHelper.create_dir_if_not_exist('/data/note/note_template')

            if FileHelper.exists_on_os('/data/report/report'):
                FileHelper.move_file_or_dir('/data/report/report', '/data/note/note')

            if FileHelper.exists_on_os('/data/report/document_template'):
                FileHelper.move_file_or_dir('/data/report/document_template', '/data/note/note_template')

            task_rename = {
                'TASK.gws_core.CreateENote': 'TASK.gws_core.CreateNoteResource',
                'TASK.gws_core.GenerateReportFromENote': 'TASK.gws_core.GenerateLabNote',
            }

            for old_typing_name, new_typing_name in task_rename.items():
                SqlMigrator.rename_process_typing_name(ResourceModel.get_db(), old_typing_name, new_typing_name)

            migrator: SqlMigrator = SqlMigrator(Note.get_db())
            migrator.add_column_if_not_exists(Note, Note.modifications)
            migrator.migrate()
