

from typing import Dict, List, Optional, Type

from peewee import ModelSelect

from gws_core.core.utils.date_helper import DateHelper
from gws_core.entity_navigator.entity_navigator import EntityNavigatorResource
from gws_core.lab.lab_config_model import LabConfigModel
from gws_core.note.note import NoteScenario
from gws_core.resource.resource_model import ResourceModel
from gws_core.scenario.scenario_zipper import ZipScenario, ZipScenarioInfo
from gws_core.scenario_template.scenario_template import ScenarioTemplate
from gws_core.scenario_template.scenario_template_factory import \
    ScenarioTemplateFactory
from gws_core.task.plug import OutputTask
from gws_core.task.task_input_model import TaskInputModel
from gws_core.user.activity.activity_dto import (ActivityObjectType,
                                                 ActivityType)
from gws_core.user.activity.activity_service import ActivityService

from ..core.classes.paginator import Paginator
from ..core.classes.search_builder import SearchBuilder, SearchParams
from ..core.decorator.transaction import transaction
from ..core.exception.exceptions import BadRequestException
from ..folder.space_folder import SpaceFolder
from ..process.process_factory import ProcessFactory
from ..protocol.protocol import Protocol
from ..protocol.protocol_model import ProtocolModel
from ..protocol.protocol_service import ProtocolService
from ..space.space_dto import SaveScenarioToSpaceDTO
from ..space.space_service import SpaceService
from ..task.task_model import TaskModel
from ..user.current_user_service import CurrentUserService
from .scenario import Scenario
from .scenario_dto import (RunningProcessInfo, RunningScenarioInfoDTO,
                           ScenarioSaveDTO)
from .scenario_enums import ScenarioCreationType, ScenarioStatus
from .scenario_search_builder import ScenarioSearchBuilder


class ScenarioService():

    ################################### CREATE ##############################

    @classmethod
    @transaction()
    def create_scenario_from_dto(cls, scenario_dto: ScenarioSaveDTO) -> Scenario:

        scenario_template: ScenarioTemplate = None
        if scenario_dto.scenario_template_id:
            scenario_template = ScenarioTemplate.get_by_id_and_check(
                scenario_dto.scenario_template_id)
        elif scenario_dto.scenario_template_json and isinstance(scenario_dto.scenario_template_json, dict):
            scenario_template = ScenarioTemplateFactory.from_export_dto_dict(
                scenario_dto.scenario_template_json)

        return cls.create_scenario(
            folder_id=scenario_dto.folder_id,
            title=scenario_dto.title,
            scenario_template=scenario_template,
            creation_type=ScenarioCreationType.MANUAL
        )

    @classmethod
    @transaction()
    def create_scenario(cls, folder_id: str = None, title: str = "",
                        scenario_template: ScenarioTemplate = None,
                        creation_type: ScenarioCreationType = ScenarioCreationType.MANUAL) -> Scenario:
        protocol_model: ProtocolModel = None

        description: Dict = None
        if scenario_template is not None:
            description = scenario_template.description
            protocol_model = ProtocolService.create_protocol_model_from_template(scenario_template)
        else:
            protocol_model = ProcessFactory.create_protocol_empty()

        folder = SpaceFolder.get_by_id_and_check(folder_id) if folder_id else None

        scenario = cls.create_scenario_from_protocol_model(
            protocol_model=protocol_model,
            folder=folder,
            title=title,
            description=description,
            creation_type=creation_type
        )

        ActivityService .add(
            ActivityType.CREATE,
            object_type=ActivityObjectType.SCENARIO,
            object_id=scenario.id
        )

        return scenario

    @classmethod
    @transaction()
    def create_scenario_from_protocol_model(
            cls, protocol_model: ProtocolModel, folder: SpaceFolder = None, title: str = "", description: Dict = None,
            creation_type: ScenarioCreationType = ScenarioCreationType.MANUAL) -> Scenario:
        if not isinstance(protocol_model, ProtocolModel):
            raise BadRequestException(
                "An instance of ProtocolModel is required")
        scenario = Scenario()
        scenario.title = title.strip()
        scenario.description = description
        scenario.folder = folder
        scenario.creation_type = creation_type

        scenario = scenario.save()

        # Set the scenario for the protocol_model and childs and save them
        protocol_model.set_scenario(scenario)
        protocol_model.save_full()
        return scenario

    @classmethod
    def create_scenario_from_protocol_type(
            cls, protocol_type: Type[Protocol],
            folder: SpaceFolder = None, title: str = "", creation_type: ScenarioCreationType = ScenarioCreationType.
            MANUAL) -> Scenario:

        protocol_model: ProtocolModel = ProtocolService.create_protocol_model_from_type(
            protocol_type=protocol_type)
        return cls.create_scenario_from_protocol_model(
            protocol_model=protocol_model, folder=folder, title=title, creation_type=creation_type)

    ################################### UPDATE ##############################

    @classmethod
    def update_scenario_title(cls, scenario_id: str, title: str) -> Scenario:
        scenario: Scenario = Scenario.get_by_id_and_check(scenario_id)

        scenario.check_is_updatable()
        scenario.title = title.strip()
        scenario = scenario.save()

        ActivityService.add_or_update_async(ActivityType.UPDATE,
                                            object_type=ActivityObjectType.SCENARIO,
                                            object_id=scenario.id)

        return scenario

    @classmethod
    def update_scenario_folder(cls, scenario_id: str, folder_id: Optional[str],
                               check_note: bool = True) -> Scenario:
        scenario: Scenario = Scenario.get_by_id_and_check(scenario_id)

        scenario.check_is_updatable()

        scenario = cls._update_scenario_folder(scenario, folder_id, check_notes=check_note)

        ActivityService.add_or_update_async(ActivityType.UPDATE,
                                            object_type=ActivityObjectType.SCENARIO,
                                            object_id=scenario.id)

        return scenario

    @classmethod
    @transaction()
    def _update_scenario_folder(cls, scenario: Scenario,
                                new_folder_id: Optional[str],
                                check_notes: bool) -> Scenario:
        folder_changed = False
        folder_removed = False
        old_folder: SpaceFolder = scenario.folder

        new_folder: SpaceFolder = None
        # update the folder
        if new_folder_id:
            new_folder = SpaceFolder.get_by_id_and_check(new_folder_id)

            if scenario.last_sync_at is not None and new_folder != scenario.folder:
                raise BadRequestException(
                    "You can't change the folder of an scenario that has been synced. Please unlink the scenario from the folder first.")

            if scenario.folder != new_folder:
                folder_changed = True

        if scenario.folder is not None and new_folder_id is None:
            folder_removed = True

        scenario.folder = new_folder

        # update scenario
        scenario = scenario.save()

        # update generated resources folder
        if folder_changed or folder_removed:
            resources: List[ResourceModel] = ResourceModel.get_by_scenario(
                scenario.id)
            for resource in resources:
                resource.folder = scenario.folder
                resource.save()

        # if the folder was removed
        if folder_removed:
            if scenario.last_sync_at is not None:
                cls._unsynchronize_with_space(scenario, old_folder.id,
                                              check_notes=check_notes)

        return scenario

    @classmethod
    def update_scenario_description(cls, id_: str, description: Dict) -> Scenario:
        scenario: Scenario = Scenario.get_by_id_and_check(id_)

        scenario.check_is_updatable()
        scenario.description = description
        scenario = scenario.save()

        ActivityService.add_or_update_async(ActivityType.UPDATE,
                                            object_type=ActivityObjectType.SCENARIO,
                                            object_id=scenario.id)

        return scenario

    @classmethod
    def reset_scenario(cls, scenario: Scenario) -> Scenario:
        scenario = scenario.reset()

        ActivityService.add_or_update_async(ActivityType.UPDATE,
                                            object_type=ActivityObjectType.SCENARIO,
                                            object_id=scenario.id)

        return scenario

    ###################################  VALIDATION  ##############################

    @classmethod
    @transaction()
    def validate_scenario_by_id(cls, id: str, folder_id: str = None) -> Scenario:
        scenario: Scenario = Scenario.get_by_id_and_check(id)

        # set the folder if it is provided
        if folder_id is not None:
            scenario.folder = SpaceFolder.get_by_id_and_check(folder_id)

        return cls.validate_scenario(scenario)

    @classmethod
    @transaction()
    def validate_scenario(cls, scenario: Scenario) -> Scenario:
        scenario.validate()

        ActivityService.add(ActivityType.VALIDATE,
                            object_type=ActivityObjectType.SCENARIO,
                            object_id=scenario.id)

        # send the scenario to the space
        cls._synchronize_with_space(scenario)

        return scenario.save()

    ###################################  SYNCHRO WITH SPACE  ##############################

    @classmethod
    def synchronize_with_space_by_id(cls, id: str) -> Scenario:
        scenario: Scenario = Scenario.get_by_id_and_check(id)
        scenario = cls._synchronize_with_space(scenario)
        return scenario.save()

    @classmethod
    def _synchronize_with_space(cls, scenario: Scenario) -> Scenario:
        # if Settings.is_local_env():
        #     Logger.info('Skipping sending scenario to space as we are running in LOCAL')
        #     return scenario

        if scenario.folder is None:
            raise BadRequestException(
                "The scenario must be linked to a folder before validating it")

        scenario.last_sync_at = DateHelper.now_utc()
        scenario.last_sync_by = CurrentUserService.get_and_check_current_user()

        lab_config: LabConfigModel = scenario.lab_config
        if lab_config is None:
            lab_config = LabConfigModel.get_current_config()
        save_scenario_dto = SaveScenarioToSpaceDTO(
            scenario=scenario.to_dto(),
            protocol=scenario.export_protocol(),
            lab_config=lab_config.to_dto()
        )
        # Save the scenario in space
        SpaceService.save_scenario(
            scenario.folder.id, save_scenario_dto)
        return scenario

    @classmethod
    @transaction()
    def _unsynchronize_with_space(cls, scenario: Scenario, folder_id: str,
                                  check_notes: bool) -> Scenario:

        if check_notes:
            synced_associated_notes = NoteScenario.find_synced_notes_by_scenario(scenario.id)

            if len(synced_associated_notes) > 0:
                raise BadRequestException(
                    "You can't unsynchronize an scenario that has associated notes synced in space. Please unsync the notes first.")

        # Delete the scenario in space
        SpaceService.delete_scenario(folder_id, scenario.id)

        # clear sync info
        scenario.last_sync_at = None
        scenario.last_sync_by = None
        return scenario.save()

    ################################### ARCHIVE  ##############################

    @classmethod
    @transaction()
    def archive_scenario_by_id(cls, id: str) -> Scenario:
        scenario: Scenario = Scenario.get_by_id_and_check(id)

        if scenario.is_archived:
            raise BadRequestException("The scenario is already archived")

        if scenario.is_running:
            raise BadRequestException("You can't archive an scenario that is running")

        ActivityService.add(
            ActivityType.ARCHIVE,
            object_type=ActivityObjectType.SCENARIO,
            object_id=id
        )

        return scenario.archive(archive=True)

    @classmethod
    def unarchive_scenario_by_id(cls, id: str) -> Scenario:
        scenario: Scenario = Scenario.get_by_id_and_check(id)

        if not scenario.is_archived:
            raise BadRequestException("The scenario is not archived")

        ActivityService.add(
            ActivityType.UNARCHIVE,
            object_type=ActivityObjectType.SCENARIO,
            object_id=id
        )

        return scenario.archive(archive=False)

    ################################### GET  ##############################

    @classmethod
    def count_of_running_scenarios(cls) -> int:
        """
        :return: the count of scenario in progress or waiting for a cli process
        :rtype: `int`
        """

        return Scenario.count_running_scenarios()

    @classmethod
    def count_running_or_queued_scenarios(cls) -> int:
        return Scenario.count_running_or_queued_scenarios()

    @classmethod
    def count_queued_scenarios(cls) -> int:
        return Scenario.count_queued_scenarios()

    @classmethod
    def get_by_id_and_check(cls, id: str) -> Scenario:
        return Scenario.get_by_id_and_check(id)

    @classmethod
    def search(cls,
               search: SearchParams,
               page: int = 0,
               number_of_items_per_page: int = 20) -> Paginator[Scenario]:

        search_builder: SearchBuilder = ScenarioSearchBuilder()

        return search_builder.add_search_params(search).search_page(page, number_of_items_per_page)

    @classmethod
    def count_by_title(cls,
                       title: str) -> int:

        return Scenario.select().where(Scenario.title == title.strip()).count()

    @classmethod
    def search_by_title(cls,
                        title: str,
                        page: int = 0,
                        number_of_items_per_page: int = 20) -> Paginator[Scenario]:

        model_select: ModelSelect = Scenario.select().where(Scenario.title.contains(title))
        return Paginator(
            model_select, page=page, nb_of_items_per_page=number_of_items_per_page)

    @classmethod
    def get_next_scenarios_of_resource(cls, resource_id: str,
                                       page: int = 0,
                                       number_of_items_per_page: int = 20) -> Paginator[Scenario]:
        """ Return the list of scenario that used the resource as input

        :param resource_id: _description_
        :type resource_id: str
        :return: _description_
        :rtype: Paginator[Scenario]
        """

        resource_model: ResourceModel = ResourceModel.get_by_id_and_check(resource_id)

        resource_navigator = EntityNavigatorResource(resource_model)
        return Paginator(resource_navigator.get_next_scenarios_select_model(),
                         page=page, nb_of_items_per_page=number_of_items_per_page)

    @classmethod
    def get_running_scenarios(cls) -> List[RunningScenarioInfoDTO]:
        scenarios: List[Scenario] = list(
            Scenario.select().where(
                # consider the WAITING_FOR_CLI_PROCESS as running
                Scenario.status.in_([ScenarioStatus.RUNNING, ScenarioStatus.WAITING_FOR_CLI_PROCESS])).order_by(
                Scenario.last_modified_at.desc()))

        return [cls.get_running_scenario_info(scenario) for scenario in scenarios]

    @classmethod
    def get_running_scenario_info(cls, scenario: Scenario) -> RunningScenarioInfoDTO:
        tasks: List[TaskModel] = scenario.get_running_tasks()

        running_tasks: List[RunningProcessInfo] = []
        for task in tasks:
            running_task = RunningProcessInfo(id=task.id,
                                              title=task.get_name(),
                                              last_message=task.get_last_message(),
                                              progression=task.get_progress_value())
            running_tasks.append(running_task)

        return RunningScenarioInfoDTO(
            id=scenario.id,
            title=scenario.title,
            folder=scenario.folder.to_dto() if scenario.folder else None,
            running_tasks=running_tasks,
        )

    ################################### COPY  ##############################

    @classmethod
    @transaction()
    def clone_scenario(cls, scenario_id: str) -> Scenario:
        """ Copy the scenario into a new draft scenario
        """
        scenario: Scenario = Scenario.get_by_id_and_check(scenario_id)

        new_scenario: Scenario = cls.create_scenario_from_protocol_model(
            protocol_model=ProtocolService.copy_protocol(
                scenario.protocol_model),
            folder=scenario.folder,
            title=scenario.title + " copy",
        )

        new_scenario.description = scenario.description
        return new_scenario.save()

    ################################### DELETE ##############################

    @classmethod
    @transaction()
    def delete_scenario(cls, scenario_id: str) -> None:

        scenario: Scenario = Scenario.get_by_id_and_check(scenario_id)

        scenario.delete_instance()

        # if the scenario was sync with space, delete it in space too
        if scenario.last_sync_at is not None and scenario.folder is not None:
            SpaceService.delete_scenario(
                scenario.folder.id, scenario.id)

        ActivityService.add(activity_type=ActivityType.DELETE,
                            object_type=ActivityObjectType.SCENARIO,
                            object_id=scenario.id)

    ################################### INTERMEDIATE RESOURCES ##############################

    @classmethod
    @transaction()
    def delete_intermediate_resources(cls, scenario_id: str) -> None:
        """Delete the intermediate resources of an scenario
        An intermediate resource is a resource that is not used as input or output and not flagged

        :param scenario_id: id of the scenario
        :type scenario_id: str
        """

        intermediate_resources: List[ResourceModel] = cls.get_intermediate_results(
            scenario_id)

        if not intermediate_resources:
            raise BadRequestException("No intermediate resources found for the scenario")

        # check if all the intermediate resources where already deleted
        if all(resource.content_is_deleted for resource in intermediate_resources):
            raise BadRequestException("All the intermediate resources are already deleted")

        # check if the intermediate resources are used in other scenarios
        resoure_navigator = EntityNavigatorResource(intermediate_resources)
        if resoure_navigator.get_next_scenarios().has_entities():
            raise BadRequestException(
                "Some intermediate resources are used in other scenarios")

        # delete the intermediate resources content
        for resource in intermediate_resources:
            resource.delete_resource_content()

        ActivityService.add(activity_type=ActivityType.DELETE_SCENARIO_INTERMEDIATE_RESOURCES,
                            object_type=ActivityObjectType.SCENARIO,
                            object_id=scenario_id)

    @classmethod
    def get_intermediate_results(cls, scenario_id: str) -> List[ResourceModel]:
        """Retrieve the list of intermediate resources of an scenario
        A resource is considered as intermediate if it is not used as output and not flagged

        :param scenario_id: id of the scenario
        :type scenario_id: str
        :return: _description_
        :rtype: List[ResourceModel]
        """
        not_flagged_resources: List[ResourceModel] = list(
            ResourceModel.get_resource_by_scenario_and_flag(scenario_id, False)
        )

        intermediate_resources: List[ResourceModel] = []
        for resource in not_flagged_resources:
            # check if the resource is used as output
            task_input_model = TaskInputModel.get_by_resource_model_and_task_type(
                resource.id, OutputTask.get_typing_name())

            # if the resource is not used as output, it is an intermediate resource
            if not task_input_model:
                intermediate_resources.append(resource)

        return intermediate_resources

    ################################### EXPORT / IMPORT ##############################

    @classmethod
    def export_scenario(cls, scenario_id: str) -> ZipScenarioInfo:
        scenario: Scenario = Scenario.get_by_id_and_check(scenario_id)

        experimeny_zip = ZipScenario(
            id=scenario.id,
            title=scenario.title,
            description=scenario.description,
            status=scenario.status,
            folder=scenario.folder.to_dto() if scenario.folder is not None else None,
            error_info=scenario.error_info
        )

        return ZipScenarioInfo(
            zip_version=1,
            scenario=experimeny_zip,
            protocol=scenario.export_protocol(),
        )
