from fastapi.param_functions import Depends

from gws_core.core.classes.paginator import Paginator
from gws_core.core.classes.search_builder import SearchParams
from gws_core.core.model.model_dto import PageDTO
from gws_core.core_controller import core_app
from gws_core.form.form_dto import (
    CreateFormDTO,
    FormDTO,
    FormSaveEventDTO,
    FormSaveResultDTO,
    SaveFormDTO,
    UpdateFormDTO,
)
from gws_core.form.form_save_event import FormSaveEvent
from gws_core.form.form_service import FormService
from gws_core.user.authorization_service import AuthorizationService


@core_app.post("/form", tags=["Form"], summary="Create a form from a published template version")
def create(
    data: CreateFormDTO,
    _=Depends(AuthorizationService.check_user_access_token),
) -> FormDTO:
    return FormService.create(data).to_dto()


@core_app.get(
    "/form/{id_}",
    tags=["Form"],
    summary="Get a form with its values and per-computed-field errors",
    response_model=None,
)
def get_full(
    id_: str,
    _=Depends(AuthorizationService.check_user_access_token),
) -> FormSaveResultDTO:
    return FormService.get_full(id_)


@core_app.put(
    "/form/{id_}",
    tags=["Form"],
    summary="Update a form (name)",
)
def update(
    id_: str,
    body: UpdateFormDTO,
    _=Depends(AuthorizationService.check_user_access_token),
) -> FormDTO:
    return FormService.update(id_, body).to_dto()


@core_app.post(
    "/form/{id_}/save",
    tags=["Form"],
    summary="Save form values; optional status_transition to SUBMITTED",
    response_model=None,
)
def save(
    id_: str,
    body: SaveFormDTO,
    _=Depends(AuthorizationService.check_user_access_token),
) -> FormSaveResultDTO:
    return FormService.save(id_, body)


@core_app.post(
    "/form/{id_}/submit",
    tags=["Form"],
    summary="Submit a form (sugar for save + status_transition=SUBMITTED)",
    response_model=None,
)
def submit(
    id_: str,
    _=Depends(AuthorizationService.check_user_access_token),
) -> FormSaveResultDTO:
    return FormService.submit(id_)


@core_app.delete(
    "/form/{id_}",
    tags=["Form"],
    summary="Delete a form",
)
def delete(
    id_: str,
    _=Depends(AuthorizationService.check_user_access_token),
) -> None:
    FormService.hard_delete(id_)


@core_app.post(
    "/form/search",
    tags=["Form"],
    summary="Advanced search for forms",
)
def search(
    search_dict: SearchParams,
    page: int | None = 1,
    number_of_items_per_page: int | None = 20,
    _=Depends(AuthorizationService.check_user_access_token),
) -> PageDTO[FormDTO]:
    return FormService.search(search_dict, page, number_of_items_per_page).to_dto()


@core_app.put(
    "/form/{id_}/archive",
    tags=["Form"],
    summary="Archive a form",
)
def archive(
    id_: str,
    _=Depends(AuthorizationService.check_user_access_token),
) -> FormDTO:
    return FormService.archive(id_).to_dto()


@core_app.put(
    "/form/{id_}/unarchive",
    tags=["Form"],
    summary="Unarchive a form",
)
def unarchive(
    id_: str,
    _=Depends(AuthorizationService.check_user_access_token),
) -> FormDTO:
    return FormService.unarchive(id_).to_dto()


@core_app.get(
    "/form/{id_}/history",
    tags=["Form"],
    summary="Get the form save-event history (one row per save)",
)
def get_history(
    id_: str,
    page: int | None = 1,
    number_of_items_per_page: int | None = 20,
    _=Depends(AuthorizationService.check_user_access_token),
) -> PageDTO[FormSaveEventDTO]:
    paginator: Paginator[FormSaveEvent] = FormService.get_history(
        id_, page, number_of_items_per_page
    )
    return paginator.to_dto()
