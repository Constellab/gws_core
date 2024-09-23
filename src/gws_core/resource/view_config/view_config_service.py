

from threading import Thread
from typing import List

from peewee import ModelSelect

from gws_core.config.config import Config
from gws_core.core.decorator.transaction import transaction
from gws_core.core.utils.date_helper import DateHelper
from gws_core.entity_navigator.entity_navigator_type import EntityType
from gws_core.model.typing_style import TypingStyle
from gws_core.note.note_view_model import NoteViewModel
from gws_core.resource.view.view_dto import ViewTypeDTO
from gws_core.resource.view.view_helper import ViewHelper
from gws_core.tag.entity_tag_list import EntityTagList
from gws_core.tag.tag_dto import TagOriginType

from ...core.classes.paginator import Paginator
from ...core.classes.search_builder import SearchBuilder, SearchParams
from ..resource_model import ResourceModel
from ..view.view import View
from ..view.view_types import ViewType, exluded_views_in_note
from .view_config import ViewConfig
from .view_config_search_builder import ViewConfigSearchBuilder


class ViewConfigService():

    MAX_HISTORY_SIZE = 5000

    @classmethod
    def get_by_id(cls, id_: str) -> ViewConfig:
        return ViewConfig.get_by_id_and_check(id_)

    @classmethod
    @transaction()
    def save_view_config(cls, resource_model: ResourceModel, view: View,
                         view_name: str, config: Config,
                         is_favorite: bool = False,
                         view_style: TypingStyle = None) -> ViewConfig:
        view_meta_data = ViewHelper.get_and_check_view_meta(resource_model.get_and_check_resource_type(), view_name)

        view_config: ViewConfig = ViewConfig(
            resource_model=resource_model,
            experiment=resource_model.experiment,
            title=view.get_title() or resource_model.name,
            view_name=view_meta_data.method_name,
            view_type=view.get_type(),
            config_values={},
            is_favorite=is_favorite or view.is_favorite(),
            config=config,
            style=view_style
        )

        # check is the view config already exists
        view_config_db = ViewConfig.get_same_view_config(view_config)

        # if not, create it
        if view_config_db is None:
            view_config_db = view_config.save()
        else:
            # refresh the last modified date
            view_config_db.last_modified_at = DateHelper.now_utc()
            # refresh style
            view_config_db.style = view_style
            view_config_db = view_config_db.save()

        # Copy the resource tags to the view config
        resource_tags = EntityTagList.find_by_entity(EntityType.RESOURCE, resource_model.id)
        tag_propagated = resource_tags.build_tags_propagated(TagOriginType.RESOURCE_PROPAGATED, resource_model.id)
        view_config_tags = EntityTagList.find_by_entity(EntityType.VIEW, view_config_db.id)
        view_config_tags.add_tags(tag_propagated)

        # limit the length without blocking the thread
        thread = Thread(target=cls._limit_length_history)
        thread.start()

        return view_config_db

    @classmethod
    def _limit_length_history(cls) -> None:
        # limit the length of the history
        if (ViewConfig.select().count() > cls.MAX_HISTORY_SIZE):
            to_delete: List[ViewConfig] = cls.get_old_views_to_delete()

            for view_config in to_delete:
                view_config.delete_instance()

    @classmethod
    def get_old_views_to_delete(cls) -> List[ViewConfig]:
        """ return the 100 oldest view config that are not favorite and not used in a note"""
        return list(ViewConfig.select().left_outer_join(NoteViewModel).where(
            (ViewConfig.is_favorite == False) & (NoteViewModel.note.is_null(True))).order_by(
            ViewConfig.last_modified_at.asc()).limit(100))

    @classmethod
    def update_title(cls, view_config_id: str, title: str) -> ViewConfig:
        view_config: ViewConfig = ViewConfig.get_by_id_and_check(view_config_id)
        view_config.title = title
        return view_config.save()

    @classmethod
    def update_favorite(cls, view_config_id: str, is_favorite: bool) -> ViewConfig:
        view_config: ViewConfig = ViewConfig.get_by_id_and_check(view_config_id)
        view_config.is_favorite = is_favorite
        return view_config.save()

    ############################################ SEARCH ############################################

    @classmethod
    def search(cls, search: SearchParams,
               page: int = 0, number_of_items_per_page: int = 20) -> Paginator[ViewConfig]:

        search_builder: SearchBuilder = ViewConfigSearchBuilder()

        return cls._search(search_builder, search, page, number_of_items_per_page)

    @classmethod
    def search_by_note(cls, note_id: str, search: SearchParams,
                       page: int = 0, number_of_items_per_page: int = 20) -> Paginator[ViewConfig]:
        from ...note.note_service import NoteService

        search_builder: SearchBuilder = ViewConfigSearchBuilder()

        # retrieve resources associated to the note's experiments
        # It retrieves the resources used as input or output of the experiments
        resources: List[ResourceModel] = NoteService.get_resources_of_associated_experiments(note_id)
        search_builder.add_expression(ViewConfig.resource_model.in_(resources))

        # exclude the type of view that are not useful in historic
        search_builder.add_expression(ViewConfig.view_type.not_in(exluded_views_in_note))

        return cls._search(search_builder, search, page, number_of_items_per_page)

    @classmethod
    def _search(cls, search_builder: SearchBuilder, search: SearchParams,
                page: int = 0, number_of_items_per_page: int = 20) -> Paginator[ViewConfig]:

        # # if the include not favorite is not checked, filter favorite
        if not search.get_filter_criteria_value("include_not_favorite"):
            search_builder.add_expression(ViewConfig.is_favorite == True)
        search.remove_filter_criteria("include_not_favorite")

        model_select: ModelSelect = search_builder.add_search_params(search).build_search()
        return Paginator(
            model_select, page=page, nb_of_items_per_page=number_of_items_per_page)

     ############################################ GET ############################################

    @classmethod
    def get_by_resource(cls, resource_id: str,
                        favorite: bool = False,
                        page: int = 0,
                        number_of_items_per_page: int = 20) -> Paginator[ViewConfig]:

        query: ModelSelect = None
        if favorite:
            query = ViewConfig.get_by_resource_and_favorite(resource_id).order_by(ViewConfig.last_modified_at.desc())
        else:
            query = ViewConfig.get_by_resource(resource_id).order_by(ViewConfig.last_modified_at.desc())

        paginator: Paginator[ViewConfig] = Paginator(
            query, page=page, nb_of_items_per_page=number_of_items_per_page)

        return paginator

    ############################# VIEW TYPE  ###########################

    @classmethod
    def get_all_view_types(cls) -> List[ViewTypeDTO]:
        view_types_dto: List[ViewTypeDTO] = []
        for view_type in ViewType:
            if view_type in [ViewType.VIEW, ViewType.EMPTY, ViewType.TABULAR]:
                continue
            view_types_dto.append(ViewTypeDTO(
                type=view_type,
                human_name=view_type.get_human_name(),
                style=view_type.get_typing_style()
            ))

        # sort by human name
        view_types_dto.sort(key=lambda x: x.human_name)

        return view_types_dto
