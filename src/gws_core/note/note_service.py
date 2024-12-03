

from typing import Callable, List

from peewee import ModelSelect

from gws_core.core.utils.date_helper import DateHelper
from gws_core.core.utils.settings import Settings
from gws_core.entity_navigator.entity_navigator_type import EntityType
from gws_core.folder.space_folder import SpaceFolder
from gws_core.impl.rich_text.rich_text import RichText
from gws_core.impl.rich_text.rich_text_file_service import RichTextFileService
from gws_core.impl.rich_text.rich_text_types import (
    RichTextBlockModificationWithUserDTO, RichTextBlockType, RichTextDTO,
    RichTextModificationType, RichTextObjectType, RichTextParagraphHeaderLevel,
    RichTextResourceViewData, RichTextUserDTO, RichTextViewFileData)
from gws_core.lab.lab_config_model import LabConfigModel
from gws_core.note.note_view_model import NoteViewModel
from gws_core.note_template.note_template import NoteTemplate
from gws_core.resource.resource_model import ResourceModel
from gws_core.resource.resource_service import ResourceService
from gws_core.resource.view.view_types import exluded_views_in_note
from gws_core.resource.view_config.view_config import ViewConfig
from gws_core.resource.view_config.view_config_service import ViewConfigService
from gws_core.scenario.scenario_service import ScenarioService
from gws_core.space.space_dto import (SaveNoteToSpaceDTO,
                                      SpaceNoteRichTextFileViewData)
from gws_core.tag.entity_tag_list import EntityTagList
from gws_core.tag.tag_dto import TagOriginType
from gws_core.task.task_input_model import TaskInputModel
from gws_core.user.activity.activity_dto import (ActivityObjectType,
                                                 ActivityType)
from gws_core.user.activity.activity_service import ActivityService
from gws_core.user.current_user_service import CurrentUserService
from gws_core.user.user_service import UserService

from ..core.classes.paginator import Paginator
from ..core.classes.search_builder import SearchBuilder, SearchParams
from ..core.decorator.transaction import transaction
from ..core.exception.exceptions.bad_request_exception import \
    BadRequestException
from ..core.exception.gws_exceptions import GWSException
from ..scenario.scenario import Scenario
from ..space.space_service import SpaceService
from .note import Note, NoteScenario
from .note_dto import NoteInsertTemplateDTO, NoteSaveDTO
from .note_search_builder import NoteSearchBuilder


class NoteService():

    @classmethod
    @transaction()
    def create(cls, note_dto: NoteSaveDTO, scenario_ids: List[str] = None) -> Note:
        note = Note()
        note.title = note_dto.title
        note.folder = SpaceFolder.get_by_id_and_check(note_dto.folder_id) if note_dto.folder_id else None

        if note_dto.template_id:
            template: NoteTemplate = NoteTemplate.get_by_id_and_check(note_dto.template_id)
            note.content = template.content

            # copy the storage of the note template to the note
            RichTextFileService.copy_object_dir(RichTextObjectType.NOTE_TEMPLATE,
                                                template.id,
                                                RichTextObjectType.NOTE,
                                                note.id)

        else:
            # Set default content for note
            note.content = RichText.create_rich_text_dto(
                [RichText.create_header("0", "Introduction", RichTextParagraphHeaderLevel.HEADER_1),
                 RichText.create_paragraph("1", ""),
                 RichText.create_paragraph("2", ""),
                 RichText.create_header("3", "Methods", RichTextParagraphHeaderLevel.HEADER_1),
                 RichText.create_paragraph("4", ""),
                 RichText.create_paragraph("5", ""),
                 RichText.create_header("6", "Results", RichTextParagraphHeaderLevel.HEADER_1),
                 RichText.create_paragraph("7", ""),
                 RichText.create_paragraph("8", ""),
                 RichText.create_header("9", "Conclusion", RichTextParagraphHeaderLevel.HEADER_1),
                 RichText.create_paragraph("10", ""),
                 RichText.create_paragraph("11", ""),
                 RichText.create_header("12", "References", RichTextParagraphHeaderLevel.HEADER_1),
                 RichText.create_paragraph("13", "")
                 ])

        note.save()

        if scenario_ids is not None:
            # Create the NoteScenario
            for scenario_id in scenario_ids:
                cls.add_scenario(note.id, scenario_id)

        ActivityService.add(ActivityType.CREATE,
                            object_type=ActivityObjectType.NOTE,
                            object_id=note.id)

        return note

    @classmethod
    def update(cls, note_id: str, note_dto: NoteSaveDTO) -> Note:
        note: Note = cls._get_and_check_before_update(note_id)

        note.title = note_dto.title.strip()

        cls._update_note_folder(note, note_dto.folder_id)

        note = note.save()

        ActivityService.add_or_update_async(ActivityType.UPDATE,
                                            object_type=ActivityObjectType.NOTE,
                                            object_id=note.id)

        return note

    @classmethod
    def update_title(cls, note_id: str, title: str) -> Note:
        note: Note = cls._get_and_check_before_update(note_id)

        note.title = title.strip()

        note = note.save()

        ActivityService.add_or_update_async(ActivityType.UPDATE,
                                            object_type=ActivityObjectType.NOTE,
                                            object_id=note.id)

        return note

    @classmethod
    def update_folder(cls, note_id: str, folder_id: str) -> Note:
        note: Note = cls._get_and_check_before_update(note_id)

        note = cls._update_note_folder(note, folder_id)

        note = note.save()

        ActivityService.add_or_update_async(ActivityType.UPDATE,
                                            object_type=ActivityObjectType.NOTE,
                                            object_id=note.id)

        return note

    @classmethod
    @transaction()
    def _update_note_folder(cls, note: Note, folder_id: str) -> Note:
        # update folder
        if folder_id:
            folder = SpaceFolder.get_by_id_and_check(folder_id)
            if note.last_sync_at is not None and folder != note.folder:
                raise BadRequestException(
                    "You can't change the folder of note that has been synced. You must unlink it from the folder first.")
            note.folder = folder

        # if the folder was removed
        if folder_id is None and note.folder is not None:

            if note.last_sync_at is not None:
                cls._unsynchronize_with_space(note, note.folder.id)
            note.folder = None

        # check that all linked scenario are in same folder
        scenarios: List[Scenario] = cls.get_scenarios_by_note(note.id)

        for scenario in scenarios:
            exp_folder_id = scenario.folder.id if scenario.folder else None
            if exp_folder_id != folder_id:
                ScenarioService.update_scenario_folder(scenario.id,
                                                       folder_id, check_note=False)

        return note

    @classmethod
    @transaction()
    def update_content(cls, note_id: str, note_content: RichTextDTO) -> Note:
        note: Note = cls._get_and_check_before_update(note_id)

        if not Settings.get_instance().is_test and not Settings.get_instance().is_local_env():
            note.modifications = SpaceService.get_modifications(note.content, note_content, note.modifications)
        note.content = note_content

        # refresh NoteResource table
        cls._refresh_note_views_and_tags(note)

        note = note.save()
        ActivityService.add_or_update_async(ActivityType.UPDATE,
                                            object_type=ActivityObjectType.NOTE,
                                            object_id=note.id)

        return note

    @classmethod
    @transaction()
    def insert_template(cls, note_id: str, data: NoteInsertTemplateDTO) -> Note:
        note: Note = cls._get_and_check_before_update(note_id)

        template: NoteTemplate = NoteTemplate.get_by_id_and_check(data.note_template_id)

        note_rich_text = note.get_content_as_rich_text()
        template_rich_text = template.get_content_as_rich_text()

        index = data.block_index
        for block in template_rich_text.get_blocks():
            note_rich_text.insert_block_at_index(index, block)
            index += 1

        note = cls.update_content(note_id, note_rich_text.to_dto())

        # copy the storage of the note template to the note
        # copy after to avoid copy if error during update_content
        RichTextFileService.copy_object_dir(RichTextObjectType.NOTE_TEMPLATE,
                                            template.id,
                                            RichTextObjectType.NOTE,
                                            note.id)
        return note

    @classmethod
    @transaction()
    def add_view_to_content(cls, note_id: str, view_config_id: str) -> Note:
        note: Note = cls._get_and_check_before_update(note_id)

        view_config: ViewConfig = ViewConfigService.get_by_id(view_config_id)

        if view_config.view_type in exluded_views_in_note:
            raise BadRequestException("You can't add this type of view to a note")

        # create the json object for the rich text
        view_content: RichTextResourceViewData = view_config.to_rich_text_resource_view()

        # get the rich text and add the resource view
        rich_text = note.get_content_as_rich_text()
        rich_text.add_resource_view(view_content)

        return cls.update_content(note_id, rich_text.to_dto())

    @classmethod
    def delete(cls, note_id: str) -> None:
        # delete the object in the database
        cls._delete_note_db(note_id)

        # if transaction is successful, delete the object in the file system
        RichTextFileService.delete_object_dir(RichTextObjectType.NOTE, note_id)

    @classmethod
    @transaction()
    def _delete_note_db(cls, note_id: str) -> None:
        note: Note = cls._get_and_check_before_update(note_id)

        Note.delete_by_id(note_id)
        EntityTagList.delete_by_entity(EntityType.NOTE, note_id)

        # if the note was sync with space, delete it in space too
        if note.last_sync_at is not None and note.folder is not None:
            SpaceService.delete_note(note.folder.id, note.id)

        ActivityService.add(ActivityType.DELETE,
                            object_type=ActivityObjectType.NOTE,
                            object_id=note_id)

    @classmethod
    @transaction()
    def _validate(cls, note_id: str, folder_id: str = None) -> Note:
        note: Note = cls._get_and_check_before_update(note_id)

        rich_text = note.get_content_as_rich_text()
        if rich_text.is_empty():
            raise BadRequestException('The note is empty')

        # set the folder if it is provided
        if folder_id is not None:
            note.folder = SpaceFolder.get_by_id_and_check(folder_id)

        if note.folder is None:
            raise BadRequestException("The note must be associated to a folder to be validated")

        if note.folder.children.count() > 0:
            raise BadRequestException(
                "The scenario must be associated with a leaf folder (folder with no children)")

        # refresh the associated views and scenario (for precaution)
        cls._refresh_note_views_and_tags(note)

        # check that all linked scenario are validated and are in same folder
        scenarios: List[Scenario] = cls.get_scenarios_by_note(note_id)
        for scenario in scenarios:
            if scenario.folder and scenario.folder.id != note.folder.id:
                raise BadRequestException(GWSException.NOTE_VALIDATION_EXP_OTHER_FOLDER.value,
                                          GWSException.NOTE_VALIDATION_EXP_OTHER_FOLDER.name, {'title': scenario.title})

        # check that all resource views are from resource that
        # were generated by scenarios that are linked to the note
        resource_views: List[RichTextResourceViewData] = rich_text.get_resource_views_data()
        scenario_ids = [scenario.id for scenario in scenarios]
        for resource_view in resource_views:
            resource = ResourceService.get_by_id_and_check(resource_view["resource_id"])

            view_name = resource_view.get("title") or resource.name
            # If the resource was generated by an scenario, check that the scenario is linked to the note
            if not resource.is_manually_generated():
                if not resource.scenario.id in scenario_ids:
                    # get the best name for the error
                    raise BadRequestException(GWSException.NOTE_VALIDATION_RESOURCE_GENERATED_VIEW_OTHER_EXP.value,
                                              GWSException.NOTE_VALIDATION_RESOURCE_GENERATED_VIEW_OTHER_EXP.name,
                                              {'view_name': view_name, 'exp_title': resource.scenario.title})
            else:
                if not TaskInputModel.resource_is_used_by_scenario(resource.id, scenario_ids):
                    raise BadRequestException(GWSException.NOTE_VALIDATION_RESOURCE_UPLOADED_VIEW_OTHER_EXP.value,
                                              GWSException.NOTE_VALIDATION_RESOURCE_UPLOADED_VIEW_OTHER_EXP.name,
                                              {'view_name': view_name, 'resource_name': resource.name})

        # validate scenario that were not validated
        for scenario in scenarios:
            if not scenario.is_validated:
                scenario.folder = note.folder
                ScenarioService.validate_scenario(scenario)

        note.validate()

        ActivityService.add(ActivityType.VALIDATE,
                            object_type=ActivityObjectType.NOTE,
                            object_id=note.id)

        return note.save()

    @classmethod
    @transaction()
    def validate_and_send_to_space(cls, note_id: str, folder_id: str = None) -> Note:
        note = cls._validate(note_id, folder_id)

        note = cls._synchronize_with_space(note)

        return note.save()

    ###################################  SYNCHRO WITH SPACE  ##############################
    @classmethod
    def synchronize_with_space_by_id(cls, id: str) -> Note:
        note: Note = cls.get_by_id_and_check(id)

        # retrieve the scenario ids
        scenarios: List[Scenario] = cls.get_scenarios_by_note(note.id)
        # syncronize the scenarios that are not validated
        for scenario in scenarios:
            if not scenario.is_validated:
                ScenarioService.synchronize_with_space_by_id(scenario.id)

        note = cls._synchronize_with_space(note)
        return note.save()

    @classmethod
    def _synchronize_with_space(cls, note: Note) -> Note:
        # if Settings.is_local_env():
        #     Logger.info('Skipping sending note to space as we are running in LOCAL')
        #     return note

        if note.folder is None:
            raise BadRequestException("The scenario must be linked to a folder before validating it")

        note.last_sync_at = DateHelper.now_utc()
        note.last_sync_by = CurrentUserService.get_and_check_current_user()

        # retrieve the scenario ids
        scenarios: List[Scenario] = cls.get_scenarios_by_note(note.id)

        lab_config: LabConfigModel = note.lab_config or LabConfigModel.get_current_config()

        save_note_dto = SaveNoteToSpaceDTO(
            note=note.to_full_dto(),
            scenario_ids=[scenario.id for scenario in scenarios],
            lab_config=lab_config.to_dto(),
            resource_views={}
        )

        rich_text = note.get_content_as_rich_text()

        # retrieve all the figures file path
        file_paths: List[str] = []

        for figure in rich_text.get_figures_data():
            file_paths.append(RichTextFileService.get_figure_file_path(RichTextObjectType.NOTE, note.id,
                                                                       figure['filename']))

        for file in rich_text.get_files_data():
            file_paths.append(RichTextFileService.get_uploaded_file_path(RichTextObjectType.NOTE, note.id,
                                                                         file['name']))

        # set the resource views in the json object
        for resource_view in rich_text.get_resource_views_data():
            # set the json view in the resource_views object
            # with the view id as key
            view_result = ResourceService.get_and_call_view_on_resource_model(
                resource_view["resource_id"],
                resource_view["view_method_name"],
                resource_view["view_config"])
            save_note_dto.resource_views[resource_view["id"]] = view_result.to_dto()

        # set the file views in the json object
        for file_view_block in rich_text.get_blocks_by_type(RichTextBlockType.FILE_VIEW):

            data: RichTextViewFileData = file_view_block.data

            # retrieve the file view
            view_result_dto = RichTextFileService.get_file_view(RichTextObjectType.NOTE,
                                                                note.id,
                                                                data["filename"])
            save_note_dto.resource_views[data["id"]] = view_result_dto

            # replace the block info with the new data to have a simpler object in space
            new_data: SpaceNoteRichTextFileViewData = {
                "id": data["id"],
                "title": data.get("title"),
                "caption": data.get("caption")
            }
            rich_text.replace_block_data_by_id(file_view_block.id, new_data)

        # Save the scenario in space
        SpaceService.save_note(note.folder.id, save_note_dto, file_paths)

        return note

    @classmethod
    def _unsynchronize_with_space(cls, note: Note, folder_id: str) -> Note:
        # delete the note in space
        SpaceService.delete_note(folder_id=folder_id, note_id=note.id)

        note.last_sync_at = None
        note.last_sync_by = None

        return note

    ###################################  LINKED SCENARIO  ##############################

    @classmethod
    @transaction()
    def add_scenario(cls, note_id: str, scenario_id: str) -> Scenario:
        note: Note = cls._get_and_check_before_update(note_id)

        note_exp: NoteScenario = NoteScenario.find_by_pk(scenario_id, note_id).first()

        # If the scenario was already added to the note
        if note_exp is not None:
            raise BadRequestException(GWSException.NOTE_EXP_ALREADY_LINKED.value,
                                      GWSException.NOTE_EXP_ALREADY_LINKED.name)

        scenario: Scenario = Scenario.get_by_id_and_check(scenario_id)

        # check folders
        if note.folder is None:
            # if the note is not associated with a folder, associate it with the folder of the scenario
            if scenario.folder is not None:
                note.folder = scenario.folder
                note.save()
        else:
            # check if the note folder is the same as the scenario folder
            if scenario.folder is not None and note.folder.id != scenario.folder.id:
                raise BadRequestException(GWSException.NOTE_ADD_EXP_OTHER_FOLDER.value,
                                          GWSException.NOTE_ADD_EXP_OTHER_FOLDER.name)

        NoteScenario.create_obj(scenario, note).save()

        # add the scenario tags to the note
        scenario_tags = EntityTagList.find_by_entity(EntityType.SCENARIO, scenario.id)
        propagated_tags = scenario_tags.build_tags_propagated(TagOriginType.SCENARIO_PROPAGATED, scenario.id)
        note_tags = EntityTagList.find_by_entity(EntityType.NOTE, note.id)
        note_tags.add_tags(propagated_tags)

        return scenario

    @classmethod
    def remove_scenario(cls, note_id: str, scenario_id: str) -> None:
        note = cls._get_and_check_before_update(note_id)

        rich_text = note.get_content_as_rich_text()
        note_views = rich_text.get_resource_views_data()

        # if any of the view is from the scenario, raise an error
        for note_view in note_views:
            if note_view.get('scenario_id') == scenario_id:
                raise BadRequestException(GWSException.NOTE_HAS_A_VIEW_FROM_SCENARIO.value,
                                          GWSException.NOTE_HAS_A_VIEW_FROM_SCENARIO.name)

        NoteScenario.delete_obj(scenario_id, note_id)

        # remove the scenario tags from the note
        scenario_tags = EntityTagList.find_by_entity(EntityType.SCENARIO, scenario_id)
        propagated_tags = scenario_tags.build_tags_propagated(TagOriginType.SCENARIO_PROPAGATED, scenario_id)
        note_tags = EntityTagList.find_by_entity(EntityType.NOTE, note_id)
        note_tags.delete_tags(propagated_tags)

    @classmethod
    def _get_and_check_before_update(cls, note_id: str) -> Note:
        """Retrieve the note and check if it's updatable or deletable

        :param note_id: [description]
        :type note_id: str
        :raises BadRequestException: [description]
        :return: [description]
        :rtype: Note
        """
        note: Note = Note.get_by_id_and_check(note_id)

        note.check_is_updatable()

        return note

    ################################################# GET ########################################

    @classmethod
    def get_by_id_and_check(cls, id: str) -> Note:
        return Note.get_by_id_and_check(id)

    @classmethod
    def get_by_scenario(cls, scenario_id: str) -> List[Note]:
        return list(Note.select().join(NoteScenario).where(
            NoteScenario.scenario == scenario_id).order_by(
            Note.last_modified_at.desc()))

    @classmethod
    def get_scenarios_by_note(cls, note_id: str) -> List[Scenario]:
        return list(Scenario.select().join(NoteScenario).where(
            NoteScenario.note == note_id).order_by(
            Scenario.last_modified_at.desc()))

    @classmethod
    def search(cls,
               search: SearchParams,
               page: int = 0,
               number_of_items_per_page: int = 20) -> Paginator[Note]:

        search_builder: SearchBuilder = NoteSearchBuilder()

        return search_builder.add_search_params(search).search_page(page, number_of_items_per_page)

    @classmethod
    def search_by_name(cls, name: str,
                       page: int = 0,
                       number_of_items_per_page: int = 20) -> Paginator[Note]:
        model_select = Note.select().where(Note.title.contains(name))

        return Paginator(
            model_select, page=page, nb_of_items_per_page=number_of_items_per_page)

    @classmethod
    def get_by_resource(cls, resource_id: str,
                        page: int = 0,
                        number_of_items_per_page: int = 20) -> Paginator[Note]:

        query = NoteViewModel.get_by_resource(resource_id)

        paginator: Paginator[NoteViewModel] = Paginator(
            query, page=page, nb_of_items_per_page=number_of_items_per_page)

        map_function: Callable[[NoteViewModel], Note] = lambda x: x.note
        paginator.map_result(map_function)
        return paginator

    ################################################# Resource View ########################################

    @classmethod
    def get_resources_of_associated_scenarios(cls, note_id: str) -> List[ResourceModel]:
        """Method to retrieve the resources of the scenarios associated with a note.
        Resources used as input or output of the scenarios are returned.
        """
        # add a filter on scenarios of the note
        scenarios = NoteService.get_scenarios_by_note(note_id)

        if len(scenarios) == 0:
            raise BadRequestException(GWSException.NOTE_NO_LINKED_SCENARIO.value,
                                      GWSException.NOTE_NO_LINKED_SCENARIO.name)

        scenario_ids = [scenario.id for scenario in scenarios]

        # retrieve the resources associated with the scenarios
        resources = ResourceService.get_scenarios_resources(scenario_ids)
        return resources

    @classmethod
    def _refresh_note_views_and_tags(cls, note: Note) -> None:
        """Method to refresh the associated views of a note. It will remove unassociated resources and
        add the new ones.
        It also refresh the tags of the note based on the tags of the associated views
        It also refresh the associated scenarios of the note
        """

        note_views: List[NoteViewModel] = NoteViewModel.get_by_note(note.id)

        # extract the views id from the rich text
        rich_text_views: List[RichTextResourceViewData] = note.get_content_as_rich_text().get_resource_views_data()

        note_tags: EntityTagList = EntityTagList.find_by_entity(EntityType.NOTE, note.id)

        rich_text_view_ids = {
            rich_text_view.get('view_config_id') for rich_text_view in rich_text_views
            if 'view_config_id' in rich_text_view}

        # detect which views were removed and unassociate resource
        for note_view in note_views:
            if note_view.view.id not in rich_text_view_ids:
                note_view.delete_instance()
                # remove the tags of the view from the note
                view_tags = EntityTagList.find_by_entity(EntityType.VIEW, note_view.view.id)
                propagated_tags = view_tags.build_tags_propagated(TagOriginType.VIEW_PROPAGATED, note_view.view.id)
                note_tags.delete_tags(propagated_tags)

        # detect which views were added
        note_view_ids = {note_view.view.id for note_view in note_views}
        for rich_text_view in rich_text_views:
            if rich_text_view.get('view_config_id') is None:
                continue
            if rich_text_view.get('view_config_id') not in note_view_ids:
                # create the link in DB
                view_config = ViewConfig.get_by_id(rich_text_view.get('view_config_id'))

                if view_config:
                    NoteViewModel(note=note, view=view_config).save()
                    # add the tags of the view to the note
                    view_tags = EntityTagList.find_by_entity(EntityType.VIEW, view_config.id)
                    propagated_tags = view_tags.build_tags_propagated(TagOriginType.VIEW_PROPAGATED, view_config.id)
                    note_tags.add_tags(propagated_tags)
                    note_view_ids.add(view_config.id)

        # refresh the associated scenarios
        new_note_views: List[NoteViewModel] = NoteViewModel.get_by_note(note.id)
        associated_scenario = NoteScenario.find_scenarios_by_note(note.id)

        # detect which scenario were added
        for new_view in new_note_views:
            if new_view.view.scenario and new_view.view.scenario not in associated_scenario:
                NoteScenario.create_obj(new_view.view.scenario, note).save()
                associated_scenario.append(new_view.view.scenario)

    ################################################# ARCHIVE ########################################

    @classmethod
    @transaction()
    def archive_note(cls, note_id: str) -> Note:
        note: Note = Note.get_by_id_and_check(note_id)

        if note.is_archived:
            raise BadRequestException('The note is already archived')

        ActivityService.add(
            ActivityType.ARCHIVE,
            object_type=ActivityObjectType.NOTE,
            object_id=note_id
        )
        return note.archive(True)

    @classmethod
    @transaction()
    def unarchive_note(cls, note_id: str) -> Note:
        note: Note = Note.get_by_id_and_check(note_id)

        if not note.is_archived:
            raise BadRequestException('The note is not archived')

        ActivityService.add(
            ActivityType.UNARCHIVE,
            object_type=ActivityObjectType.NOTE,
            object_id=note_id
        )
        return note.archive(False)

    ################################################# HISTORY ########################################

    @classmethod
    def get_note_history(cls, note_id: str) -> List[RichTextBlockModificationWithUserDTO]:
        note: Note = Note.get_by_id_and_check(note_id)

        if not note.modifications:
            return []

        modifications: List[RichTextBlockModificationWithUserDTO] = []

        for modif in note.modifications.modifications:
            user = UserService.get_by_id_and_check(modif.userId)
            modifications.append(RichTextBlockModificationWithUserDTO(
                user=RichTextUserDTO(
                    id=user.id,
                    firstname=user.first_name,
                    lastname=user.last_name,
                    photo=user.photo
                ),
                userId=modif.userId,
                blockId=modif.blockId,
                blockType=modif.blockType.value,
                blockValue=modif.blockValue,
                differences=modif.differences,
                id=modif.id,
                type=modif.type.value,
                index=modif.index,
                oldIndex=modif.oldIndex,
                time=modif.time
            ))

        return modifications

    @classmethod
    def get_undo_content(cls, note_id: str, modification_id: str) -> RichTextDTO:
        note: Note = Note.get_by_id_and_check(note_id)

        return SpaceService.get_undo_content(note.content, note.modifications, modification_id)

    @classmethod
    @transaction()
    def rollback_content(cls, note_id: str, modification_id: str) -> Note:
        note: Note = Note.get_by_id_and_check(note_id)

        if note.is_archived:
            raise BadRequestException('You cannot rollback an archived note')

        rollbacked_content = cls.get_undo_content(note_id, modification_id)

        modification_index = note.modifications.modifications.index(
            next((modif for modif in note.modifications.modifications if modif.id == modification_id), None))

        modif_type = note.modifications.modifications[modification_index].type

        if not modif_type == RichTextModificationType.DELETED and not modif_type == RichTextModificationType.MOVED:
            modification_index = modification_index + 1

        note.modifications.modifications = note.modifications.modifications[:modification_index]
        note.content = rollbacked_content

        cls._refresh_note_views_and_tags(note)

        note = note.save()
        ActivityService.add_or_update_async(ActivityType.UPDATE,
                                            object_type=ActivityObjectType.NOTE,
                                            object_id=note.id)

        return note
