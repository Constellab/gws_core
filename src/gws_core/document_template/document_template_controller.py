
from typing import Optional

from fastapi.param_functions import Depends

from gws_core.core.model.model_dto import PageDTO
from gws_core.document_template.document_template_dto import (
    CreateDocumentTemplateDTO, CreateDocumentTemplateFromNoteDTO,
    DocumentTemplateDTO)
from gws_core.document_template.document_template_service import \
    DocumentTemplateService
from gws_core.impl.rich_text.rich_text_types import RichTextDTO

from ..core.classes.search_builder import SearchParams
from ..core_controller import core_app
from ..user.auth_service import AuthService


@core_app.post("/document-template", tags=["Document template"], summary="Create an empty document template")
def create_empty(data: CreateDocumentTemplateDTO, _=Depends(AuthService.check_user_access_token)) -> DocumentTemplateDTO:
    return DocumentTemplateService.create_empty(data.title).to_dto()


@core_app.post("/document-template/from-note", tags=["Document template"],
               summary="Create a document template from a note")
def create_from_note(
        data: CreateDocumentTemplateFromNoteDTO, _=Depends(AuthService.check_user_access_token)) -> DocumentTemplateDTO:
    return DocumentTemplateService.create_from_note(data.note_id).to_dto()


@core_app.put("/document-template/{doc_id}/title", tags=["Document template"],
              summary="Update the title of a document template")
def update_title(doc_id: str,
                 body: CreateDocumentTemplateDTO,
                 _=Depends(AuthService.check_user_access_token)) -> DocumentTemplateDTO:
    return DocumentTemplateService.update_title(doc_id, body.title).to_dto()


@core_app.put("/document-template/{doc_id}/content", tags=["Document template"],
              summary="Update a document template content")
def update_content(
        doc_id: str, content: RichTextDTO, _=Depends(AuthService.check_user_access_token)) -> RichTextDTO:
    return DocumentTemplateService.update_content(doc_id, content).content


@core_app.delete("/document-template/{doc_id}", tags=["Document template"], summary="Delete a notetemplate ")
def delete(doc_id: str, _=Depends(AuthService.check_user_access_token)) -> None:
    DocumentTemplateService.delete(doc_id)

################################################# GET ########################################


@core_app.get("/document-template/{id_}", tags=["Document template"],
              summary="Get a document template", response_model=None)
def get_by_id(id_: str, _=Depends(AuthService.check_user_access_token)) -> DocumentTemplateDTO:
    return DocumentTemplateService.get_by_id_and_check(id_).to_dto()


@core_app.get("/document-template/{id_}/content", tags=["Document template"],
              summary="Get a note", response_model=None)
def get_content(id_: str, _=Depends(AuthService.check_user_access_token)) -> RichTextDTO:
    return DocumentTemplateService.get_by_id_and_check(id_).content


@core_app.post("/document-template/search", tags=["Document template"],
               summary="Advanced search for document templates")
def search(search_dict: SearchParams,
           page: Optional[int] = 1,
           number_of_items_per_page: Optional[int] = 20,
           _=Depends(AuthService.check_user_access_token)) -> PageDTO[DocumentTemplateDTO]:
    """
    Advanced search on scenario
    """

    return DocumentTemplateService.search(search_dict, page, number_of_items_per_page).to_dto()


@core_app.get("/document-template/search-name/{name}", tags=["Document template"],
              summary="Search for document template by name")
def search_by_name(name: str,
                   page: Optional[int] = 1,
                   number_of_items_per_page: Optional[int] = 20,
                   _=Depends(AuthService.check_user_access_token)) -> PageDTO[DocumentTemplateDTO]:
    return DocumentTemplateService.search_by_name(name, page, number_of_items_per_page).to_dto()
