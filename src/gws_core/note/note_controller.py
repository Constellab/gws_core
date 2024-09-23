
from typing import List, Optional

from fastapi.param_functions import Depends

from gws_core.core.model.model_dto import PageDTO
from gws_core.experiment.experiment_dto import ExperimentDTO
from gws_core.impl.rich_text.rich_text_types import RichTextDTO

from ..core.classes.search_builder import SearchParams
from ..core_controller import core_app
from ..user.auth_service import AuthService
from .note_dto import NoteDTO, NoteInsertTemplateDTO, NoteSaveDTO
from .note_service import NoteService


@core_app.post("/note", tags=["Note"], summary="Create a note for an experiment")
def create(note_dto: NoteSaveDTO, _=Depends(AuthService.check_user_access_token)) -> NoteDTO:
    return NoteService.create(note_dto).to_dto()


@core_app.post("/note/experiment/{experiment_id}", tags=["Note"], summary="Create a note for an experiment")
def create_for_experiment(experiment_id: str,
                          note_dto: NoteSaveDTO,
                          _=Depends(AuthService.check_user_access_token)) -> NoteDTO:
    return NoteService.create(note_dto, [experiment_id]).to_dto()


@core_app.put("/note/{note_id}", tags=["Note"], summary="Update a note information")
def update(note_id: str, note_dto: NoteSaveDTO, _=Depends(AuthService.check_user_access_token)) -> NoteDTO:
    return NoteService.update(note_id, note_dto).to_dto()


@core_app.put("/note/{note_id}/title", tags=["Note"],
              summary="Update the title of a note")
def update_title(note_id: str,
                 body: dict,
                 _=Depends(AuthService.check_user_access_token)) -> NoteDTO:
    return NoteService.update_title(note_id, body["title"]).to_dto()


@core_app.put("/note/{note_id}/folder", tags=["Note"],
              summary="Update the folder of a note")
def update_folder(note_id: str,
                  body: dict,
                  _=Depends(AuthService.check_user_access_token)) -> NoteDTO:
    return NoteService.update_folder(note_id, body["folder_id"]).to_dto()


@core_app.put("/note/{note_id}/content", tags=["Note"], summary="Update a note content")
def update_content(note_id: str, content: RichTextDTO, _=Depends(AuthService.check_user_access_token)) -> RichTextDTO:
    return NoteService.update_content(note_id, content).content


@core_app.put("/note/{note_id}/content/insert-template", tags=["Note"],
              summary="Insert a document template in the note")
def insert_template(note_id: str,
                    data: NoteInsertTemplateDTO,
                    _=Depends(AuthService.check_user_access_token)) -> RichTextDTO:
    return NoteService.insert_template(note_id, data).content


@core_app.put("/note/{note_id}/content/add-view/{view_config_id}", tags=["Note"],
              summary="Add a view to the note")
def add_view_to_content(note_id: str, view_config_id: str,
                        _=Depends(AuthService.check_user_access_token)) -> NoteDTO:
    return NoteService.add_view_to_content(note_id, view_config_id).to_dto()


@core_app.delete("/note/{note_id}", tags=["Note"], summary="Delete a note")
def delete(note_id: str, _=Depends(AuthService.check_user_access_token)) -> None:
    NoteService.delete(note_id)


@core_app.put(
    "/note/{note_id}/add-experiment/{experiment_id}", tags=["Note"],
    summary="Add an experiment to the note")
def add_experiment(note_id: str, experiment_id: str, _=Depends(AuthService.check_user_access_token)) -> ExperimentDTO:
    return NoteService.add_experiment(note_id, experiment_id).to_dto()


@core_app.delete(
    "/note/{note_id}/remove-experiment/{experiment_id}", tags=["Note"],
    summary="Remove an experiment")
def remove_experiment(
        note_id: str, experiment_id: str, _=Depends(AuthService.check_user_access_token)) -> None:
    NoteService.remove_experiment(note_id, experiment_id)


@core_app.put("/note/{note_id}/validate/{folder_id}", tags=["Note"], summary="Validate the note")
def validate(note_id: str, folder_id: Optional[str] = None,
             _=Depends(AuthService.check_user_access_token)) -> NoteDTO:
    return NoteService.validate_and_send_to_space(note_id, folder_id).to_dto()


@core_app.put('/note/{note_id}/sync-with-space', tags=["Note"], summary="Sync the note with space")
def sync_with_space(note_id: str,
                    _=Depends(AuthService.check_user_access_token)) -> NoteDTO:
    return NoteService.synchronize_with_space_by_id(note_id).to_dto()


################################################# GET ########################################


@core_app.get("/note/{id_}", tags=["Note"], summary="Get a note")
def get_by_id(id_: str, _=Depends(AuthService.check_user_access_token)) -> NoteDTO:
    return NoteService.get_by_id_and_check(id_).to_dto()


@core_app.get("/note/{id_}/content", tags=["Note"], summary="Get the note content",)
def get_content(id_: str, _=Depends(AuthService.check_user_access_token)) -> RichTextDTO:
    return NoteService.get_by_id_and_check(id_).content


@core_app.get("/note/experiment/{experiment_id}", tags=["Note"],
              summary="Find notes of an experiment")
def get_by_experiment(experiment_id: str, _=Depends(AuthService.check_user_access_token)) -> List[NoteDTO]:
    notes = NoteService.get_by_experiment(experiment_id)
    return [note.to_dto() for note in notes]


@core_app.get("/note/{note_id}/experiments", tags=["Note"],
              summary="Find experiments of a note")
def get_experiment_by_note(
        note_id: str, _=Depends(AuthService.check_user_access_token)) -> List[ExperimentDTO]:
    experiments = NoteService.get_experiments_by_note(note_id)
    return [experiment.to_dto() for experiment in experiments]


@core_app.post("/note/search", tags=["Note"], summary="Advanced search for notes")
def advanced_search(search_dict: SearchParams,
                    page: Optional[int] = 1,
                    number_of_items_per_page: Optional[int] = 20,
                    _=Depends(AuthService.check_user_access_token)) -> PageDTO[NoteDTO]:
    """
    Advanced search on experiment
    """

    return NoteService.search(search_dict, page, number_of_items_per_page).to_dto()


@core_app.get("/note/search-name/{name}", tags=["Note"],
              summary="Search for note by name")
def search_by_name(name: str,
                   page: Optional[int] = 1,
                   number_of_items_per_page: Optional[int] = 20,
                   _=Depends(AuthService.check_user_access_token)) -> PageDTO[NoteDTO]:
    return NoteService.search_by_name(name, page, number_of_items_per_page).to_dto()


@core_app.get("/note/resource/{resource_id}", tags=["Note"],
              summary="Get the list of note by resource")
def get_by_resource(resource_id: str,
                    page: Optional[int] = 1,
                    number_of_items_per_page: Optional[int] = 20,
                    _=Depends(AuthService.check_user_access_token)) -> PageDTO[NoteDTO]:

    return NoteService.get_by_resource(
        resource_id=resource_id,
        page=page,
        number_of_items_per_page=number_of_items_per_page,
    ).to_dto()


################################################# ARCHIVE ########################################
@core_app.put("/note/{id_}/archive", tags=["Note"], summary="Archive a note")
def archive(id_: str, _=Depends(AuthService.check_user_access_token)) -> NoteDTO:
    return NoteService.archive_note(id_).to_dto()


@core_app.put("/note/{id_}/unarchive", tags=["Note"], summary="Unarchive a note")
def unarchive(id_: str, _=Depends(AuthService.check_user_access_token)) -> NoteDTO:
    return NoteService.unarchive_note(id_).to_dto()
