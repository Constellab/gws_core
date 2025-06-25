from gws_core.community.community_dto import (CommunityAgentFileDTO,
                                              CommunityAgentVersionDTO)
from gws_core.impl.agent.helper.agent_factory import AgentFactory
from gws_core.protocol.protocol_model import ProtocolModel
from gws_core.protocol.protocol_service import ProtocolService
from gws_core.streamlit.agents.streamlit_agent import StreamlitAgent
from gws_core.test.base_test_case import BaseTestCase


class TestAgentFactory(BaseTestCase):

    def test_generate_agent_file_from_agent_id(self):
        protocol_model: ProtocolModel = ProtocolService.create_empty_protocol()

        community_agent_version: CommunityAgentVersionDTO = CommunityAgentVersionDTO.from_json(
            {
                'id': '6f12dde5-3fc5-4b83-b5e0-3ab586eda6b2',
                'version': 2,
                'type': 'TASK.gws_core.StreamlitAgent',
                'environment': None,
                'code': '# This is a template for a streamlit agent.\n# This generates an app with one dataframe as input. Then the user can select 2 columns to plot a scatter plot.\n\nimport plotly.express as px\nimport streamlit as st\nfrom pandas import DataFrame\n\n# Your Streamlit app code here\nst.title("App example")\n\n# show a table from file_path which is a csv file full width\nif sources:\n    df: DataFrame = sources[0].get_data()\n\n    # show the dataframe\n    st.dataframe(df)\n\n    # add a select widget with the columns names with no default value\n    # set the selectbox side by side\n    col1, col2 = st.columns(2)\n\n    with col1:\n        x_col = st.selectbox("Select x column", options=df.columns, index=0)\n\n    with col2:\n        y_col = st.selectbox("Select y column", options=df.columns, index=1)\n\n    if x_col and y_col:\n        # Generate a scatter plot with plotly express\n        fig = px.scatter(df, x=x_col, y=y_col)\n        st.plotly_chart(fig)\n',
                'params': {'specs': {}, 'values': {}},
                'input_specs': {'specs': {"source": {"resource_types": [{"typing_name": "RESOURCE.gws_core.Resource", "brick_version": "0.10.0", "human_name": "Resource", "style": {"icon_technical_name": "resource", "icon_type": "MATERIAL_ICON", "background_color": "#c7c8cc", "icon_color": "#000000"}, "short_description": ""}], "human_name": "Resource", "short_description": "", "is_optional": True, "sub_class": None, "is_constant": None}}},
                'output_specs': {'specs': {"streamlit_app": {"resource_types": [{"typing_name": "RESOURCE.gws_core.StreamlitResource", "brick_version": "0.10.0", "human_name": "Streamlit App", "style": {"icon_technical_name": "dashboard", "icon_type": "MATERIAL_ICON", "background_color": "#ff4b4b", "icon_color": "#000000"}, "short_description": "Streamlit App"}], "human_name": "Streamlit app", "short_description": "Streamlit App", "is_optional": False, "sub_class": False, "is_constant": False}}},
                'config_specs': {},
                'agent': {'id': 'd4816577-94b6-4cc7-a363-52127f4e4525', 'title': 'Test Streamlit', 'latest_publish_version': 2}
            })

        ProtocolService.add_community_agent_version_to_protocol_id(
            protocol_model.id, community_agent_version)

        protocol_model = protocol_model.refresh()

        streamlit_base_process_name = StreamlitAgent().get_typing_name().split('.')[-1]

        streamlit_process = protocol_model.get_process(streamlit_base_process_name)

        agent_dict: CommunityAgentFileDTO = AgentFactory().generate_agent_file_from_agent_id(streamlit_process.id)

        self.assertEqual(agent_dict.code, community_agent_version.code)
        self.assertEqual(agent_dict.config_specs, community_agent_version.config_specs)
        self.assertEqual(agent_dict.params.to_json_dict(), community_agent_version.params)
        self.assertIsNotNone(agent_dict.bricks)
        self.assertEqual(agent_dict.task_type == 'STREAMLIT', True)
