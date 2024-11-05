
from typing import List

import streamlit as st

from gws_core import (Folder, ResourceModel, ScenarioProxy,
                      ScenarioSearchBuilder, Tag)
from gws_core.scenario.scenario import Scenario
from gws_core.streamlit import ResourceSearchInput

st.title("Hello World")

default_resource = ResourceModel.get_by_id_and_check('f3aa406d-bac6-468c-aa96-19b0cc0b5ad9')

selected_resource: ResourceModel | None = ResourceSearchInput().add_flagged_filter(
    True).add_is_archived_filter(False) \
    .add_order_by(ResourceModel.name) \
    .select(placeholder="Search for folder")

if selected_resource:
    st.write(selected_resource)

    if isinstance(selected_resource, ResourceModel):
        st.write("Is ResourceModel")

# search_scenario_builder = ScenarioSearchBuilder().add_tag_filter(
#     Tag(key='test', value='test')).add_is_archived_filter(False)

# list_scenario: List[Scenario] = search_scenario_builder.search_all()

# scenario_proxy = ScenarioProxy.from_existing_scenario("ID du scenario")

# scenario_proxy.add_to_queue()
