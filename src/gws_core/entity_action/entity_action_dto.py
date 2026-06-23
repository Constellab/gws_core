from typing import Literal

from gws_core.config.param.param_types import ParamSpecDTO
from gws_core.core.model.model_dto import BaseModelDTO

# Matches the Angular ThemePalette used by the front dynamic menu.
EntityActionColor = Literal["primary", "accent", "warn"]


class EntityActionButtonDTO(BaseModelDTO):
    """Menu button. Mirrors the front ``FlMenuDynamicButton``.

    Instead of an ``onClick`` callback, it carries an ``action_name`` that the
    front sends back to ``POST /entity-action/{entity_type}/{id}/{action_name}``.
    """

    type: Literal["button"] = "button"
    text: str
    action_name: str
    icon: str | None = None
    divider: bool = False
    disabled: bool = False
    color: EntityActionColor | None = None
    children: list["EntityActionMenuDTO"] | None = None
    # When set, the front renders a form from these specs on click and POSTs the
    # collected values as the body of the execute request. Null/absent means the
    # button has no form (click POSTs immediately). Same shape as the credentials
    # form (produced by ConfigSpecs.to_dto()).
    config_specs: dict[str, ParamSpecDTO] | None = None


class EntityActionLinkDTO(BaseModelDTO):
    """Menu link to an internal route. Mirrors the front ``FlMenuDynamicLink``."""

    type: Literal["link"] = "link"
    text: str
    link: str
    icon: str | None = None
    divider: bool = False
    color: EntityActionColor | None = None


EntityActionMenuDTO = EntityActionButtonDTO | EntityActionLinkDTO

# resolve the forward reference used by EntityActionButtonDTO.children
EntityActionButtonDTO.model_rebuild()


class EntityActionResultDTO(BaseModelDTO):
    """Result returned after executing an action.

    All fields are optional: the front applies the navigation if ``navigate_to``
    is set and shows ``message`` if provided.
    """

    navigate_to: str | None = None
    navigate_query_params: dict | None = None
    open_in_new_tab: bool = False
    message: str | None = None
