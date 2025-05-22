

from typing import Any, Dict, List, Optional

import streamlit as st

from gws_core.resource.resource_model import ResourceModel
from gws_core.streamlit.components.streamlit_component_loader import \
    StreamlitComponentLoader
from gws_core.streamlit.widgets.streamlit_state import StreamlitState


class StreamlitResourceSelect():
    """ Streamlit component to select a resource
    This component is a wrapper around the GWS resource search component.
    It allows the user to search and select a resource.
    """

    _streamlit_component_loader = StreamlitComponentLoader("select-resource")
    filters: Dict[str, Any] = {}
    column_tags_filter_keys: List[str] = []

    def __init__(self):
        self.filters = {}
        self.column_tags_filter_keys = []

    def add_tag_filter(self, key: str, value: Any = None) -> None:
        if 'tags' not in self.filters:
            self.filters['tags'] = []
        tag = {'key': key, 'value': value} if value is not None else {'key': key}
        self.filters['tags'].append(tag)

    def add_column_tag_filter_key(self, key: str) -> None:
        self.column_tags_filter_keys.append(key)

    def include_not_flagged_resources(self) -> None:
        """ Add a filter to include not flagged resources """
        self.filters['includeNotFlagged'] = True

    def select_resource(self, placeholder: str = 'Search for resource',
                        key='resource-select',
                        defaut_resource: ResourceModel = None) -> Optional[ResourceModel]:
        """ Create a search box to select a resource

        :param placeholder: Placeholder for empty searches shown within the component, defaults to 'Search for resource'
        :type placeholder: str, optional
        :param defaut_resource: default resource to show, defaults to None
        :type defaut_resource: ResourceModel, optional
        :return: _description_
        :rtype: Optional[ResourceModel]
        """

        data = {
            "default_resource": defaut_resource.to_dto() if defaut_resource is not None else None,
            "placeholder": placeholder,
            "default_filters": self.filters,
            "column_tags_filter_keys": self.column_tags_filter_keys,
        }

        component_value = self._streamlit_component_loader.call_component(
            data, key=key, authentication_info=StreamlitState.get_user_auth_info())

        if component_value is None:
            st.session_state['__gws_resource_model__'] = None
            return None

        if 'resourceId' in component_value:
            resource_id = component_value['resourceId']
            if resource_id is None:
                st.session_state['__gws_resource_model__'] = None
                return None
            resource_model = ResourceModel.get_by_id_and_check(resource_id)

            st.session_state['__gws_resource_model__'] = resource_model

        return st.session_state.get('__gws_resource_model__')
