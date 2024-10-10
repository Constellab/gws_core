
from typing import Optional

from fastapi.param_functions import Depends

from gws_core.core.model.model_dto import PageDTO
from gws_core.impl.rich_text.rich_text_types import RichTextDTO
from gws_core.note_template.note_template_dto import (
    CreateNoteTemplateDTO, CreateNoteTemplateFromNoteDTO, NoteTemplateDTO)
from gws_core.note_template.note_template_service import NoteTemplateService

from ..core.classes.search_builder import SearchParams
from ..core_controller import core_app
from ..user.auth_service import AuthService


@core_app.post("/note-template", tags=["Note template"], summary="Create an empty note template")
def create_empty(data: CreateNoteTemplateDTO, _=Depends(AuthService.check_user_access_token)) -> NoteTemplateDTO:
    return NoteTemplateService.create_empty(data.title).to_dto()


@core_app.post("/note-template/from-note", tags=["Note template"],
               summary="Create a note template from a note")
def create_from_note(
        data: CreateNoteTemplateFromNoteDTO, _=Depends(AuthService.check_user_access_token)) -> NoteTemplateDTO:
    return NoteTemplateService.create_from_note(data.note_id).to_dto()


@core_app.put("/note-template/{doc_id}/title", tags=["Note template"],
              summary="Update the title of a note template")
def update_title(doc_id: str,
                 body: CreateNoteTemplateDTO,
                 _=Depends(AuthService.check_user_access_token)) -> NoteTemplateDTO:
    return NoteTemplateService.update_title(doc_id, body.title).to_dto()


@core_app.put("/note-template/{doc_id}/content", tags=["Note template"],
              summary="Update a note template content")
def update_content(
        doc_id: str, content: RichTextDTO, _=Depends(AuthService.check_user_access_token)) -> RichTextDTO:
    return NoteTemplateService.update_content(doc_id, content).content


@core_app.delete("/note-template/{doc_id}", tags=["Note template"], summary="Delete a notetemplate ")
def delete(doc_id: str, _=Depends(AuthService.check_user_access_token)) -> None:
    NoteTemplateService.delete(doc_id)

################################################# GET ########################################


@core_app.get("/note-template/{id_}", tags=["Note template"],
              summary="Get a note template", response_model=None)
def get_by_id(id_: str, _=Depends(AuthService.check_user_access_token)) -> NoteTemplateDTO:
    return NoteTemplateService.get_by_id_and_check(id_).to_dto()


@core_app.get("/note-template/{id_}/content", tags=["Note template"],
              summary="Get a note", response_model=None)
def get_content(id_: str, _=Depends(AuthService.check_user_access_token)) -> RichTextDTO:
    return NoteTemplateService.get_by_id_and_check(id_).content


@core_app.post("/note-template/search", tags=["Note template"],
               summary="Advanced search for note templates")
def search(search_dict: SearchParams,
           page: Optional[int] = 1,
           number_of_items_per_page: Optional[int] = 20,
           _=Depends(AuthService.check_user_access_token)) -> PageDTO[NoteTemplateDTO]:
    """
    Advanced search on scenario
    """

    return NoteTemplateService.search(search_dict, page, number_of_items_per_page).to_dto()


@core_app.get("/note-template/search-name/{name}", tags=["Note template"],
              summary="Search for note template by name")
def search_by_name(name: str,
                   page: Optional[int] = 1,
                   number_of_items_per_page: Optional[int] = 20,
                   _=Depends(AuthService.check_user_access_token)) -> PageDTO[NoteTemplateDTO]:
    return NoteTemplateService.search_by_name(name, page, number_of_items_per_page).to_dto()
