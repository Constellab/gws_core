# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from threading import Thread
from typing import Any, Dict, List

from gws_core.config.param_spec_helper import ParamSpecHelper
from gws_core.resource.view_helper import ViewHelper
from gws_core.resource.view_types import ViewType
from gws_core.user.current_user_service import CurrentUserService
from peewee import ModelSelect

from ...core.classes.paginator import Paginator
from ...core.classes.search_builder import SearchBuilder, SearchParams
from ...core.utils.logger import Logger
from ...task.transformer.transformer_type import TransformerDict
from ...user.user import User
from ..resource_model import ResourceModel
from ..view import View
from .view_config import ViewConfig
from .view_config_search_builder import ViewConfigSearchBuilder


class ViewConfigService():

    MAX_HISTORY_SIZE = 100

    @classmethod
    def save_view_config_in_async(cls, resource_model: ResourceModel, view: View,
                                  view_name: str, config_values: Dict[str, Any],
                                  transformers: List[TransformerDict] = None) -> None:
        """Save a view config in the db asynchronously (it doesn't stop current thread)
        """
        thread = Thread(target=cls.save_view_config, args=(resource_model, view, view_name,
                                                           config_values, transformers, CurrentUserService.get_and_check_current_user()))
        thread.start()

    @classmethod
    def save_view_config(cls, resource_model: ResourceModel, view: View,
                         view_name: str, config_values: Dict[str, Any],
                         transformers: List[TransformerDict] = None, user: User = None) -> None:
        try:

            if user:
                CurrentUserService.set_current_user(user)

            view_meta_data = ViewHelper.get_and_check_view(resource_model.get_resource_type(), view_name)

            # merge config with specs of the view method and the view
            config = {
                **ParamSpecHelper.get_and_check_values(view_meta_data.specs, config_values),
                **ParamSpecHelper.get_and_check_values(view._specs, config_values)}

            view_config: ViewConfig = ViewConfig(
                resource_model=resource_model,
                experiment=resource_model.experiment,
                title=view.get_title(),
                view_name=view_meta_data.method_name,
                view_type=view.get_type(),
                config_values=config,
                transformers=transformers,
            )

            # check is the view config already exists
            view_config_db = ViewConfig.get_same_view_config(view_config)

            # if not, create it
            if view_config_db is None:
                view_config.save()
            else:
                # otherwise, refresh last modified date
                view_config_db.save()

            # limite the length of the history
            if(ViewConfig.select().count() > cls.MAX_HISTORY_SIZE):
                last_view_config: ViewConfig = ViewConfig.select().order_by(ViewConfig.last_modified_at.asc()).first()
                last_view_config.delete_instance()
        except Exception as err:
            Logger.error('Error while saving view config', err)
            Logger.log_exception_stack_trace(err)

    @classmethod
    def search(cls, search: SearchParams,
               page: int = 0, number_of_items_per_page: int = 20) -> Paginator[ResourceModel]:

        search_builder: SearchBuilder = ViewConfigSearchBuilder()

        model_select: ModelSelect = search_builder.build_search(search)
        return Paginator(
            model_select, page=page, number_of_items_per_page=number_of_items_per_page)

    @classmethod
    def search_by_resources(cls, resource_ids: List[str], view_types: List[ViewType], search: SearchParams,
                            page: int = 0, number_of_items_per_page: int = 20) -> Paginator[ResourceModel]:

        search_builder: SearchBuilder = ViewConfigSearchBuilder()

        # filter on resource ids
        search_builder.add_expression(ViewConfig.resource_model.in_(resource_ids))

        # filter on view type
        search_builder.add_expression(ViewConfig.view_type.in_(view_types))

        model_select: ModelSelect = search_builder.build_search(search)
        return Paginator(
            model_select, page=page, number_of_items_per_page=number_of_items_per_page)
