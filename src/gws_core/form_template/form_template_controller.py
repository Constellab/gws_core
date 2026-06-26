from fastapi.param_functions import Depends

from gws_core.config.param.param_types import ParamSpecDTO
from gws_core.core.classes.search_builder import SearchParams
from gws_core.core.model.model_dto import PageDTO
from gws_core.core_controller import core_app
from gws_core.form_template.form_template_ai_service import FormTemplateAiService
from gws_core.form_template.form_template_dto import (
    CreateDraftVersionDTO,
    CreateFormTemplateDTO,
    FormTemplateDTO,
    FormTemplateVersionDTO,
    GenerateComputedParamDTO,
    GenerateComputedParamResultDTO,
    GenerateTemplateFieldDTO,
    GenerateTemplateFieldResultDTO,
    GenerateTemplateSpecsDTO,
    ReorderDraftFieldsDTO,
    TestFormTemplateVersionDTO,
    TestFormTemplateVersionResultDTO,
    UpdateFormTemplateDTO,
    ValidateComputedParamDTO,
    ValidateComputedParamResultDTO,
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
    summary="Get a form template",
)
def get(
    id_: str,
    _=Depends(AuthorizationService.check_user_access_token),
) -> FormTemplateDTO:
    return FormTemplateService.get_by_id_and_check(id_).to_dto()


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
    page: int = 1,
    number_of_items_per_page: int = 20,
    _=Depends(AuthorizationService.check_user_access_token),
) -> PageDTO[FormTemplateDTO]:
    return FormTemplateService.search(search_dict, page, number_of_items_per_page).to_dto(FormTemplateDTO)


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
    "/form-template/{id_}/version",
    tags=["Form template"],
    summary="List versions of a form template",
)
def list_versions(
    id_: str,
    _=Depends(AuthorizationService.check_user_access_token),
) -> list[FormTemplateVersionDTO]:
    return [v.to_dto() for v in FormTemplateService.list_versions(id_)]


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
    "/form-template/{id_}/version/{version_id}/test",
    tags=["Form template"],
    summary="Test/validate form values against a version (DRAFT allowed, no save)",
    response_model=None,
)
def test_version(
    id_: str,
    version_id: str,
    body: TestFormTemplateVersionDTO,
    _=Depends(AuthorizationService.check_user_access_token),
) -> TestFormTemplateVersionResultDTO:
    return FormTemplateService.test_version(id_, version_id, body)


@core_app.post(
    "/form-template/{id_}/version/{version_id}/field/{field_key}",
    tags=["Form template"],
    summary="Add a field to a DRAFT version",
)
def create_draft_field(
    id_: str,
    version_id: str,
    field_key: str,
    spec_dto: ParamSpecDTO,
    _=Depends(AuthorizationService.check_user_access_token),
) -> FormTemplateVersionDTO:
    return FormTemplateService.create_draft_field(
        id_, version_id, field_key, spec_dto
    ).to_dto()


@core_app.put(
    "/form-template/{id_}/version/{version_id}/field/{field_key}",
    tags=["Form template"],
    summary="Update a field of a DRAFT version",
)
def update_draft_field(
    id_: str,
    version_id: str,
    field_key: str,
    spec_dto: ParamSpecDTO,
    _=Depends(AuthorizationService.check_user_access_token),
) -> FormTemplateVersionDTO:
    return FormTemplateService.update_draft_field(
        id_, version_id, field_key, spec_dto
    ).to_dto()


@core_app.put(
    "/form-template/{id_}/version/{version_id}/field/{field_key}/rename-and-update/{new_field_key}",
    tags=["Form template"],
    summary="Rename and update a field of a DRAFT version",
)
def rename_and_update_draft_field(
    id_: str,
    version_id: str,
    field_key: str,
    new_field_key: str,
    spec_dto: ParamSpecDTO,
    _=Depends(AuthorizationService.check_user_access_token),
) -> FormTemplateVersionDTO:
    return FormTemplateService.rename_and_update_draft_field(
        id_, version_id, field_key, new_field_key, spec_dto
    ).to_dto()


@core_app.post(
    "/form-template/{id_}/version/{version_id}/computed-param/validate",
    tags=["Form template"],
    summary="Validate a candidate ComputedParam expression against a version's specs",
)
def validate_computed_param(
    id_: str,
    version_id: str,
    body: ValidateComputedParamDTO,
    _=Depends(AuthorizationService.check_user_access_token),
) -> ValidateComputedParamResultDTO:
    return FormTemplateService.validate_computed_param(id_, version_id, body)


@core_app.post(
    "/form-template/{id_}/version/{version_id}/computed-param/generate-with-ai",
    tags=["Form template"],
    summary="Generate a ComputedParam expression from a natural-language description via AI",
)
def generate_computed_param_with_ai(
    id_: str,
    version_id: str,
    body: GenerateComputedParamDTO,
    _=Depends(AuthorizationService.check_user_access_token),
) -> GenerateComputedParamResultDTO:
    return FormTemplateAiService.generate_computed_param_expression(id_, version_id, body)


@core_app.post(
    "/form-template/{id_}/version/{version_id}/generate-specs-with-ai",
    tags=["Form template"],
    summary="AI-generate or modify a DRAFT form template's fields from a description",
)
def generate_specs_with_ai(
    id_: str,
    version_id: str,
    body: GenerateTemplateSpecsDTO,
    _=Depends(AuthorizationService.check_user_access_token),
) -> FormTemplateVersionDTO:
    return FormTemplateAiService.generate_template_specs(id_, version_id, body).to_dto()


@core_app.post(
    "/form-template/{id_}/version/{version_id}/generate-field-with-ai",
    tags=["Form template"],
    summary="AI-generate or edit a single DRAFT field from a description (does not persist)",
)
def generate_field_with_ai(
    id_: str,
    version_id: str,
    body: GenerateTemplateFieldDTO,
    _=Depends(AuthorizationService.check_user_access_token),
) -> GenerateTemplateFieldResultDTO:
    return FormTemplateAiService.generate_template_field(id_, version_id, body)


@core_app.put(
    "/form-template/{id_}/version/{version_id}/fields/reorder",
    tags=["Form template"],
    summary="Reorder fields of a DRAFT version",
)
def reorder_draft_fields(
    id_: str,
    version_id: str,
    body: ReorderDraftFieldsDTO,
    _=Depends(AuthorizationService.check_user_access_token),
) -> FormTemplateVersionDTO:
    return FormTemplateService.reorder_draft_fields(
        id_, version_id, body.field_names
    ).to_dto()


@core_app.delete(
    "/form-template/{id_}/version/{version_id}/field/{field_key}",
    tags=["Form template"],
    summary="Delete a field from a DRAFT version",
)
def delete_draft_field(
    id_: str,
    version_id: str,
    field_key: str,
    _=Depends(AuthorizationService.check_user_access_token),
) -> FormTemplateVersionDTO:
    return FormTemplateService.delete_draft_field(id_, version_id, field_key).to_dto()


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
