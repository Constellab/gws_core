# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from fastapi import Depends

from gws_core.core.classes.jsonable import ListJsonable
from gws_core.core_app import core_app
from gws_core.entity_navigator.entity_navigator import (EntityNavigator,
                                                        EntityType)
from gws_core.user.auth_service import AuthService


@core_app.get("/entity-navigator/{entity_type}/{id}")
def get_entities(entity_type: EntityType, id: str, _=Depends(AuthService.check_user_access_token)):

    entity_navigator = EntityNavigator.from_entity_id(entity_type, id)

    results = entity_navigator.get_next_entities_recursive([EntityType.EXPERIMENT,
                                                            EntityType.RESOURCE, EntityType.REPORT,
                                                            EntityType.VIEW])

    return ListJsonable(list(results)).to_json()
