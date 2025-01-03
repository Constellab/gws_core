from typing import List, Optional, Type

from peewee import Expression, Ordering
from streamlit_searchbox import st_searchbox

from gws_core.resource.resource import Resource
from gws_core.resource.resource_dto import ResourceOrigin
from gws_core.resource.resource_model import ResourceModel
from gws_core.resource.resource_search_builder import ResourceSearchBuilder
from gws_core.tag.tag import Tag


class ResourceSearchInput():

    search_builder: ResourceSearchBuilder

    _default_options: List[ResourceModel] = None

    def __init__(self):
        self.search_builder = ResourceSearchBuilder()

    def select(self, placeholder: str = 'Search for resource',
               key: str = "searchbox",
               debounce: int = 300,
               label: str = None) -> Optional[ResourceModel]:
        """ Create a search box to select a resource

        :param placeholder: Placeholder for empty searches shown within the component, defaults to 'Search for resource'
        :type placeholder: str, optional
        :param key: streamlit key, defaults to "searchbox"
        :type key: str, optional
        :param debounce: _description_, defaults to 300
        :type debounce: int, optional
        :param label: Label shown above the component, defaults to None
        :type label: str, optional
        :return: _description_
        :rtype: Optional[ResourceModel]
        """

        if self._default_options is None:
            self._default_options = self.search_builder.search_all()

        selected_resource: ResourceModel = st_searchbox(
            self._search_resources,
            key=key,
            placeholder=placeholder,
            default_options=self._default_options,
            debounce=debounce,
            label=label,
        )

        return selected_resource

    # def select(self, placeholder: str = 'Search for resource',
    #            key: str = "searchbox",
    #            debounce: int = 300,
    #            label: str = None) -> Optional[ResourceModel]:
    #     """ Create a search box to select a resource

    #     :param placeholder: Placeholder for empty searches shown within the component, defaults to 'Search for resource'
    #     :type placeholder: str, optional
    #     :param key: streamlit key, defaults to "searchbox"
    #     :type key: str, optional
    #     :param debounce: _description_, defaults to 300
    #     :type debounce: int, optional
    #     :param label: Label shown above the component, defaults to None
    #     :type label: str, optional
    #     :return: _description_
    #     :rtype: Optional[ResourceModel]
    #     """

    #     search_params = st.session_state.get(key, None)

    #     resources: Paginator = None

    #     if search_params is None:
    #         resources = self.search_builder.search_page(0, 10)
    #     else:
    #         resources = self.search_builder.add_name_filter(search_params).search_page(0, 10)

    #     # selected_resource: ResourceModel = st_searchbox(
    #     #     self._search_resources,
    #     #     key=key,
    #     #     placeholder=placeholder,
    #     #     default_options=self._default_options,
    #     #     debounce=debounce,
    #     #     label=label,
    #     # )

    #     print('Init search with  ', search_params, ' ', len(resources.results))
    #     streamlit_component_loader = StreamlitComponentLoader(
    #         "dashboard-components",
    #         version="dc_1.0.0",
    #         is_released=False)

    #     component_value = streamlit_component_loader.get_function()(
    #         resources=resources.to_dto().to_json_dict(),
    #     )

    #     print('Component value ', component_value)

    #     if component_value is None:
    #         return None

    #     if 'searchParam' in component_value and component_value['searchParam']:
    #         st.session_state[key] = component_value['searchParam']
    #         rerun()
    #         return None

    #     if 'selectedResource' in component_value and component_value['selectedResource']:
    #         return component_value['selectedResource']

    #     return component_value

    def set_default_options(self, default_options: List[ResourceModel]) -> "ResourceSearchInput":
        """Set the default options for the search box, set empty list to disable
        By default, it call a search based on the current filters
        """
        self._default_options = default_options
        return self

    def add_order_by(self, order: Ordering) -> "ResourceSearchInput":
        """
        Add an ordering to the search query

        :param order: Peewee ordering object like ResourceModel.name, ResourceModel.name.asc(), ResourceModel.name.desc()
        :type order: Ordering
        :return: _description_
        :rtype: ResourceSearchInput
        """
        self.search_builder.add_ordering(order)
        return self

    def add_resource_type_filter(self, resource_type: Type[Resource]) -> "ResourceSearchInput":
        """Filter the search query by a specific resource type
        """
        self.search_builder.add_resource_type_filter(resource_type)
        return self

    def add_resource_typing_name_filter(self, resource_typing_name: str) -> "ResourceSearchInput":
        """Filter the search query by a specific resource typing name
        """
        self.search_builder.add_resource_typing_name_filter(resource_typing_name)
        return self

    def add_tag_filter(self, tag: Tag) -> "ResourceSearchInput":
        """Filter the search query by a specific tag
        """
        self.search_builder.add_tag_filter(tag)
        return self

    def add_origin_filter(self, origin: ResourceOrigin) -> "ResourceSearchInput":
        """Filter the search query by a specific origin
        """
        self.search_builder.add_origin_filter(origin)
        return self

    def add_folder_filter(self, folder_id: str) -> "ResourceSearchInput":
        """Filter the search query by a specific folder
        """
        self.search_builder.add_folder_filter(folder_id)
        return self

    def add_flagged_filter(self, flagged: bool) -> "ResourceSearchInput":
        """Filter the search query by a specific flag
        """
        self.search_builder.add_flagged_filter(flagged)
        return self

    def add_parent_filter(self, parent_id: str) -> "ResourceSearchInput":
        """Filter the search query by a specific parent
        """
        self.search_builder.add_parent_filter(parent_id)
        return self

    def add_is_archived_filter(self, is_archived: bool) -> "ResourceSearchInput":
        """Filter the search query by a specific archived status
        """
        self.search_builder.add_is_archived_filter(is_archived)
        return self

    def add_expression(self, expression: Expression) -> "ResourceSearchInput":
        """Add a peewee expression to the search query
        """
        self.search_builder.add_expression(expression)
        return self

    # function with list of labels
    def _search_resources(self, searchterm: str) -> List[ResourceModel]:
        return self.search_builder.add_name_filter(searchterm).search_all()
