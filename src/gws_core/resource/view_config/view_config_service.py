# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from threading import Thread
from typing import List

from peewee import ModelSelect

from gws_core.config.config import Config
from gws_core.core.utils.date_helper import DateHelper
from gws_core.experiment.experiment import Experiment
from gws_core.resource.view.view_helper import ViewHelper
from gws_core.resource.view.view_types import exluded_views_in_historic
from gws_core.user.current_user_service import CurrentUserService

from ...core.classes.paginator import Paginator
from ...core.classes.search_builder import (SearchBuilder,
                                            SearchFilterCriteria, SearchParams)
from ...core.utils.logger import Logger
from ...user.user import User
from ..resource_model import ResourceModel
from ..view.view import View
from .view_config import ViewConfig
from .view_config_search_builder import ViewConfigSearchBuilder


class ViewConfigService():

    MAX_HISTORY_SIZE = 5000

    @classmethod
    def get_by_id(cls, id: str) -> ViewConfig:
        return ViewConfig.get_by_id_and_check(id)

    @classmethod
    def save_view_config(cls, resource_model: ResourceModel, view: View,
                         view_name: str, config: Config,
                         flagged: bool = False,
                         user: User = None) -> ViewConfig:
        try:

            if user:
                CurrentUserService.set_current_user(user)

            view_meta_data = ViewHelper.get_and_check_view_meta(resource_model.get_resource_type(), view_name)

            view_config: ViewConfig = ViewConfig(
                resource_model=resource_model,
                experiment=resource_model.experiment,
                title=view.get_title() or resource_model.name,
                view_name=view_meta_data.method_name,
                view_type=view.get_type(),
                config_values={},
                flagged=flagged,
                config=config
            )

            # check is the view config already exists
            view_config_db = ViewConfig.get_same_view_config(view_config)

            # if not, create it
            if view_config_db is None:
                view_config_db = view_config.save()
            else:
                # refresh the last modified date
                view_config_db.last_modified_at = DateHelper.now_utc()
                view_config_db = view_config_db.save()

            # limit the length without blocking the thread
            thread = Thread(target=cls._limit_length_history)
            thread.start()

            return view_config_db
        except Exception as err:
            Logger.error(f"Error while saving view config : {err}")
            Logger.log_exception_stack_trace(err)
            return None

    @classmethod
    def _limit_length_history(cls) -> None:
        # limit the length of the history
        if (ViewConfig.select().count() > cls.MAX_HISTORY_SIZE):
            last_view_config: ViewConfig = ViewConfig.select().order_by(ViewConfig.last_modified_at.asc()).first()
            last_view_config.delete_instance()

    @classmethod
    def update_title(cls, view_config_id: str, title: str) -> ViewConfig:
        view_config: ViewConfig = ViewConfig.get_by_id_and_check(view_config_id)
        view_config.title = title
        return view_config.save()

    @classmethod
    def update_flagged(cls, view_config_id: str, flagged: bool) -> ViewConfig:
        view_config: ViewConfig = ViewConfig.get_by_id_and_check(view_config_id)
        view_config.flagged = flagged
        return view_config.save()

    ############################################ SEARCH ############################################

    @classmethod
    def search(cls, search: SearchParams,
               page: int = 0, number_of_items_per_page: int = 20) -> Paginator[ResourceModel]:

        search_builder: SearchBuilder = ViewConfigSearchBuilder()

        return cls._search(search_builder, search, page, number_of_items_per_page)

    @classmethod
    def search_for_report(cls, report_id: str, search: SearchParams,
                          page: int = 0, number_of_items_per_page: int = 20) -> Paginator[ResourceModel]:
        from ...report.report_service import ReportService

        search_builder: SearchBuilder = ViewConfigSearchBuilder()

        # retrieve resources associated to the report's experiments
        # It retrieves the resources used as input or output of the experiments
        resources: List[ResourceModel] = ReportService.get_resources_of_associated_experiments(report_id)
        search_builder.add_expression(ViewConfig.resource_model.in_(resources))

        return cls._search(search_builder, search, page, number_of_items_per_page)

    @classmethod
    def _search(cls, search_builder: SearchBuilder, search: SearchParams,
                page: int = 0, number_of_items_per_page: int = 20) -> Paginator[ResourceModel]:
        # exclude the type of view that are not useful in historic
        search_builder.add_expression(ViewConfig.view_type.not_in(exluded_views_in_historic))

        # if the include not flagged is not checked, filter flagged
        if not search.get_filter_criteria_value("include_not_flagged"):
            search_builder.add_expression(ViewConfig.flagged == True)
        search.remove_filter_criteria("include_not_flagged")

        # Handle the project filters, get all experiment of this project and filter by experiment
        projects_criteria: SearchFilterCriteria = search.get_filter_criteria('project')
        if projects_criteria is not None:
            experiments: List[Experiment] = list(Experiment.select().where(
                Experiment.project.in_(projects_criteria['value'])))
            search_builder.add_expression(ViewConfig.experiment.in_(experiments))
            search.remove_filter_criteria('project')

        model_select: ModelSelect = search_builder.build_search(search)
        return Paginator(
            model_select, page=page, nb_of_items_per_page=number_of_items_per_page)

     ############################################ GET ############################################

    @classmethod
    def get_by_resource(cls, resource_id: str,
                        flagged: bool = False,
                        page: int = 0,
                        number_of_items_per_page: int = 20) -> Paginator[ViewConfig]:

        query: ModelSelect = None
        if flagged:
            query = ViewConfig.get_by_resource_and_flagged(resource_id).order_by(ViewConfig.last_modified_at.desc())
        else:
            query = ViewConfig.get_by_resource(resource_id).order_by(ViewConfig.last_modified_at.desc())

        paginator: Paginator[ViewConfig] = Paginator(
            query, page=page, nb_of_items_per_page=number_of_items_per_page)

        return paginator
