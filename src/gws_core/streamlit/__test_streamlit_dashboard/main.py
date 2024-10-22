
from typing import List

import streamlit as st

from gws_core import (Folder, ResourceModel, ScenarioProxy,
                      ScenarioSearchBuilder, Tag)
from gws_core.scenario.scenario import Scenario
from gws_core.streamlit import ResourceSearchInput

st.title("Hello World")

selected_resource: ResourceModel | None = ResourceSearchInput().add_resource_type_filter(
    Folder).add_flagged_filter(True).add_is_archived_filter(False).select(placeholder="Search for folder")


search_scenario_builder = ScenarioSearchBuilder().add_tag_filter(
    Tag(key='test', value='test')).add_is_archived_filter(False)

list_scenario: List[Scenario] = search_scenario_builder.search_all()

scenario_proxy = ScenarioProxy.from_existing_scenario("ID du scenario")

scenario_proxy.add_to_queue()
