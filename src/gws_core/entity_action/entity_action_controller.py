from fastapi import Body, Depends

from gws_core.config.config_params import ConfigParamsDict
from gws_core.core_controller import core_app
from gws_core.entity_action.entity_action_dto import (
    EntityActionMenuDTO,
    EntityActionResultDTO,
)
from gws_core.entity_action.entity_action_service import EntityActionService
from gws_core.entity_action.entity_action_type import EntityActionType
from gws_core.user.authorization_service import AuthorizationService


@core_app.get(
    "/entity-action/{entity_type}/{entity_id}",
    tags=["Entity action"],
    summary="Get the dynamic action menu of an entity",
)
def get_entity_actions(
    entity_type: EntityActionType,
    entity_id: str,
    _=Depends(AuthorizationService.check_user_access_token),
) -> list[EntityActionMenuDTO]:
    """Return the plugin-contributed action menu items for an entity."""
    return EntityActionService.get_entity_actions(entity_type, entity_id)


@core_app.post(
    "/entity-action/{entity_type}/{entity_id}/{action_name}",
    tags=["Entity action"],
    summary="Execute a dynamic action on an entity",
)
def execute_entity_action(
    entity_type: EntityActionType,
    entity_id: str,
    action_name: str,
    config_params: ConfigParamsDict | None = Body(default=None),
    _=Depends(AuthorizationService.check_user_access_token),
) -> EntityActionResultDTO:
    """Execute the named action; the action is dispatched to its owning plugin.

    ``config_params`` is the optional dict of form values collected by the front
    when the button declared ``config_specs``. It is absent/null for buttons with
    no form and passed through to the plugin without validation.
    """
    return EntityActionService.execute_entity_action(
        entity_type, entity_id, action_name, config_params
    )
