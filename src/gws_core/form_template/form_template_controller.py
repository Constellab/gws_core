from fastapi.param_functions import Depends

from gws_core.config.param.param_spec_helper import ParamSpecHelper
from gws_core.config.param.param_types import ParamSpecDTO, ParamSpecTypeInfo
from gws_core.core.classes.search_builder import SearchParams
from gws_core.core.model.model_dto import PageDTO
from gws_core.core_controller import core_app
from gws_core.form_template.form_template_dto import (
    CreateDraftVersionDTO,
    CreateFormTemplateDTO,
    FormTemplateDTO,
    FormTemplateFullDTO,
    FormTemplateVersionDTO,
    UpdateFormTemplateDTO,
)
from gws_core.form_template.form_template_service import FormTemplateService
from gws_core.user.authorization_service import AuthorizationService


@core_app.post("/form-template", tags=["Form template"], summary="Create a form template")
def create(
    data: CreateFormTemplateDTO,
    _=Depends(AuthorizationService.check_user_access_token),
) -> FormTemplateDTO:
    return FormTemplateService.create(data).to_dto()


@core_app.get(
    "/form-template/{id_}",
    tags=["Form template"],
    summary="Get a form template with its versions",
    response_model=None,
)
def get_full(
    id_: str,
    _=Depends(AuthorizationService.check_user_access_token),
) -> FormTemplateFullDTO:
    return FormTemplateService.get_full(id_)


@core_app.put(
    "/form-template/{id_}",
    tags=["Form template"],
    summary="Update a form template",
)
def update(
    id_: str,
    body: UpdateFormTemplateDTO,
    _=Depends(AuthorizationService.check_user_access_token),
) -> FormTemplateDTO:
    return FormTemplateService.update(id_, body).to_dto()


@core_app.delete(
    "/form-template/{id_}",
    tags=["Form template"],
    summary="Delete a form template",
)
def delete(
    id_: str,
    _=Depends(AuthorizationService.check_user_access_token),
) -> None:
    FormTemplateService.hard_delete(id_)


@core_app.post(
    "/form-template/search",
    tags=["Form template"],
    summary="Advanced search for form templates",
)
def search(
    search_dict: SearchParams,
    page: int | None = 1,
    number_of_items_per_page: int | None = 20,
    _=Depends(AuthorizationService.check_user_access_token),
) -> PageDTO[FormTemplateDTO]:
    return FormTemplateService.search(search_dict, page, number_of_items_per_page).to_dto()


@core_app.put(
    "/form-template/{id_}/archive",
    tags=["Form template"],
    summary="Archive a form template",
)
def archive(
    id_: str,
    _=Depends(AuthorizationService.check_user_access_token),
) -> FormTemplateDTO:
    return FormTemplateService.archive(id_).to_dto()


@core_app.put(
    "/form-template/{id_}/unarchive",
    tags=["Form template"],
    summary="Unarchive a form template",
)
def unarchive(
    id_: str,
    _=Depends(AuthorizationService.check_user_access_token),
) -> FormTemplateDTO:
    return FormTemplateService.unarchive(id_).to_dto()


# ----------------------------- versions ---------------------------------- #


@core_app.post(
    "/form-template/{id_}/version",
    tags=["Form template"],
    summary="Create a new DRAFT version for a form template",
)
def create_draft(
    id_: str,
    body: CreateDraftVersionDTO,
    _=Depends(AuthorizationService.check_user_access_token),
) -> FormTemplateVersionDTO:
    return FormTemplateService.create_draft(id_, body).to_dto()


@core_app.get(
    "/form-template/{id_}/version/{version_id}",
    tags=["Form template"],
    summary="Get a form template version",
)
def get_version(
    id_: str,
    version_id: str,
    _=Depends(AuthorizationService.check_user_access_token),
) -> FormTemplateVersionDTO:
    return FormTemplateService.get_version(id_, version_id).to_dto()


@core_app.post(
    "/form-template/{id_}/version/{version_id}/field/{field_name}",
    tags=["Form template"],
    summary="Add a field to a DRAFT version",
)
def create_draft_field(
    id_: str,
    version_id: str,
    field_name: str,
    spec_dto: ParamSpecDTO,
    _=Depends(AuthorizationService.check_user_access_token),
) -> FormTemplateVersionDTO:
    return FormTemplateService.create_draft_field(
        id_, version_id, field_name, spec_dto
    ).to_dto()


@core_app.put(
    "/form-template/{id_}/version/{version_id}/field/{field_name}",
    tags=["Form template"],
    summary="Update a field of a DRAFT version",
)
def update_draft_field(
    id_: str,
    version_id: str,
    field_name: str,
    spec_dto: ParamSpecDTO,
    _=Depends(AuthorizationService.check_user_access_token),
) -> FormTemplateVersionDTO:
    return FormTemplateService.update_draft_field(
        id_, version_id, field_name, spec_dto
    ).to_dto()


@core_app.put(
    "/form-template/{id_}/version/{version_id}/field/{field_name}/rename-and-update/{new_field_name}",
    tags=["Form template"],
    summary="Rename and update a field of a DRAFT version",
)
def rename_and_update_draft_field(
    id_: str,
    version_id: str,
    field_name: str,
    new_field_name: str,
    spec_dto: ParamSpecDTO,
    _=Depends(AuthorizationService.check_user_access_token),
) -> FormTemplateVersionDTO:
    return FormTemplateService.rename_and_update_draft_field(
        id_, version_id, field_name, new_field_name, spec_dto
    ).to_dto()


@core_app.delete(
    "/form-template/{id_}/version/{version_id}/field/{field_name}",
    tags=["Form template"],
    summary="Delete a field from a DRAFT version",
)
def delete_draft_field(
    id_: str,
    version_id: str,
    field_name: str,
    _=Depends(AuthorizationService.check_user_access_token),
) -> FormTemplateVersionDTO:
    return FormTemplateService.delete_draft_field(id_, version_id, field_name).to_dto()


@core_app.delete(
    "/form-template/{id_}/version/{version_id}",
    tags=["Form template"],
    summary="Delete a form template version",
)
def delete_version(
    id_: str,
    version_id: str,
    _=Depends(AuthorizationService.check_user_access_token),
) -> None:
    FormTemplateService.delete_version(id_, version_id)


@core_app.post(
    "/form-template/{id_}/version/{version_id}/publish",
    tags=["Form template"],
    summary="Publish a DRAFT version",
)
def publish_version(
    id_: str,
    version_id: str,
    _=Depends(AuthorizationService.check_user_access_token),
) -> FormTemplateVersionDTO:
    return FormTemplateService.publish_version(id_, version_id).to_dto()


@core_app.post(
    "/form-template/{id_}/version/{version_id}/archive",
    tags=["Form template"],
    summary="Archive a PUBLISHED version",
)
def archive_version(
    id_: str,
    version_id: str,
    _=Depends(AuthorizationService.check_user_access_token),
) -> FormTemplateVersionDTO:
    return FormTemplateService.archive_version(id_, version_id).to_dto()


@core_app.post(
    "/form-template/{id_}/version/{version_id}/unarchive",
    tags=["Form template"],
    summary="Unarchive an ARCHIVED version",
)
def unarchive_version(
    id_: str,
    version_id: str,
    _=Depends(AuthorizationService.check_user_access_token),
) -> FormTemplateVersionDTO:
    return FormTemplateService.unarchive_version(id_, version_id).to_dto()


########################## DYNAMIC PARAM #####################
@core_app.get(
    "/form-template/config/get-param-spec-types",
    tags=["Form template"],
    summary="Get param spec types",
)
def get_param_spec_types(
    _=Depends(AuthorizationService.check_user_access_token),
) -> list[ParamSpecTypeInfo]:
    return ParamSpecHelper.get_dynamic_param_allowed_param_spec_types(True)
