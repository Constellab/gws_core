

from time import sleep

from gws_core import ResourceModel
from gws_core.community.community_dto import CommunityAgentVersionDTO
from gws_core.entity_navigator.entity_navigator_service import \
    EntityNavigatorService
from gws_core.impl.agent.py_agent import PyAgent
from gws_core.impl.robot.robot_resource import Robot
from gws_core.impl.robot.robot_tasks import RobotCreate, RobotMove
from gws_core.io.connector import Connector
from gws_core.process.process_model import ProcessModel
from gws_core.protocol.protocol_model import ProtocolModel
from gws_core.protocol.protocol_proxy import ProtocolProxy
from gws_core.protocol.protocol_service import ProtocolService
from gws_core.resource.resource_dto import ResourceOrigin
from gws_core.resource.view.viewer import Viewer
from gws_core.scenario.scenario_proxy import ScenarioProxy
from gws_core.streamlit.agents.streamlit_agent import StreamlitAgent
from gws_core.task.plug.input_task import InputTask
from gws_core.task.plug.output_task import OutputTask
from gws_core.test.base_test_case import BaseTestCase
from gws_core.user.current_user_service import CurrentUserService

from ..protocol_examples import TestNestedProtocol


# test_protocol_service
class TestProtocolService(BaseTestCase):

    def test_add_process(self):
        CurrentUserService.get_and_check_current_user()
        protocol_model: ProtocolModel = ProtocolService.create_empty_protocol()

        process_model: ProcessModel = ProtocolService.add_process_to_protocol_id(
            protocol_model.id, RobotMove.get_typing_name()).process

        protocol_model = protocol_model.refresh()
        self.assertEqual(protocol_model.get_process(
            process_model.instance_name).get_process_type(), RobotMove)

        # Test add source
        resource_model: ResourceModel = ResourceModel.save_from_resource(
            Robot.empty(), ResourceOrigin.UPLOADED)
        source_model: ProcessModel = ProtocolService.add_input_resource_to_process_input(
            protocol_model.id, resource_model.id, process_model.instance_name, 'robot').process

        protocol_model = protocol_model.refresh()
        source_model = protocol_model.get_process(
            source_model.instance_name)
        self.assertEqual(source_model.get_process_type(), InputTask)
        self.assertEqual(source_model.config.get_value(
            InputTask.config_name), resource_model.id)
        # check that the source_config_id is set for the task model
        self.assertEqual(source_model.source_config_id, resource_model.id)
        # Check that the source was automatically run
        self.assertTrue(source_model.is_finished)

        # check that the robot_move received the resource because InputTask was run
        process_model = process_model.refresh()
        self.assertEqual(process_model.in_port('robot').get_resource_model_id(), resource_model.id)

        # Check that the connector was created
        self.assertEqual(len(protocol_model.connectors), 1)

        # Test add output
        output_task_model: ProcessModel = ProtocolService.add_output_task_to_process_ouput(
            protocol_model.id, process_model.instance_name, 'robot').process
        protocol_model = protocol_model.refresh()
        output_task_model = protocol_model.get_process(output_task_model.instance_name)
        self.assertEqual(output_task_model.get_process_type(), OutputTask)

        # Check that the connector was created
        self.assertEqual(len(protocol_model.connectors), 2)

        # Test rename the process
        ProtocolService.rename_process(protocol_model.id, process_model.instance_name, 'New super name')
        process_model = process_model.refresh()
        self.assertEqual(process_model.name, 'New super name')

    def test_add_viewer(self):
        protocol_model: ProtocolModel = ProtocolService.create_empty_protocol()

        process_model: ProcessModel = ProtocolService.add_process_to_protocol_id(
            protocol_model.id, RobotMove.get_typing_name()).process

        # Test add view task
        viewer_model = ProtocolService.add_viewer_to_process_output(
            protocol_model.id, process_model.instance_name, 'robot').process
        protocol_model = protocol_model.refresh()

        viewer_model = protocol_model.get_process(viewer_model.instance_name)
        self.assertEqual(viewer_model.get_process_type(), Viewer)
        # check that the view task was pre-configured with the robot type
        self.assertEqual(viewer_model.config.get_value(
            Viewer.resource_config_name), Robot.get_typing_name())

        # Check that the connector was created
        self.assertEqual(len(protocol_model.connectors), 1)

    def test_connector(self):
        protocol_model: ProtocolModel = ProtocolService.create_empty_protocol()

        create: ProcessModel = ProtocolService.add_process_to_protocol_id(
            protocol_model.id, RobotCreate.get_typing_name()).process
        move: ProcessModel = ProtocolService.add_process_to_protocol_id(
            protocol_model.id, RobotMove.get_typing_name()).process

        ProtocolService.add_connector_to_protocol_id(
            protocol_model.id, create.instance_name, 'robot', move.instance_name, 'robot')

        protocol_model = protocol_model.refresh()

        # Check that the connector was created
        self.assertEqual(len(protocol_model.connectors), 1)
        connector: Connector = protocol_model.connectors[0]

        # Check the port of the connector
        self.assertEqual(connector.left_port_name, 'robot')
        self.assertEqual(connector.left_process.id, create.id)
        self.assertEqual(connector.right_port_name, 'robot')
        self.assertEqual(connector.right_process.id, move.id)

        # Test removing connector
        ProtocolService.delete_connector_of_protocol(
            protocol_model.id, move.instance_name, 'robot')

        protocol_model = protocol_model.refresh()

        # Check that the connector was deleted
        self.assertEqual(len(protocol_model.connectors), 0)

    def test_reset_process(self):

        scenario = ScenarioProxy(TestNestedProtocol)
        scenario.run()
        self.assertTrue(scenario.get_model().is_success)

        # reset a process of the sub protocol
        main_protocol: ProtocolProxy = scenario.get_protocol()
        sub_protocol: ProtocolProxy = main_protocol.get_process('mini_proto')

        # Get resources and check that they exist
        main_resource_to_clear: ResourceModel = main_protocol.get_process(
            'p5').get_output_resource_model('robot')
        sub_resource_to_keep: ResourceModel = sub_protocol.get_process(
            'p1').get_output_resource_model('robot')
        sub_resource_to_clear: ResourceModel = sub_protocol.get_process(
            'p3').get_output_resource_model('robot')
        self.assertIsNotNone(main_resource_to_clear.refresh())
        self.assertIsNotNone(sub_resource_to_keep.refresh())
        self.assertIsNotNone(sub_resource_to_clear.refresh())

        impact_result = EntityNavigatorService.check_impact_for_process_reset(
            sub_protocol.get_model().id, 'p2')
        self.assertFalse(impact_result.has_entities())
        EntityNavigatorService.reset_process_of_protocol_id(
            sub_protocol.get_model().id, 'p2')

        # check that all the next processes of p2 are reset
        main_protocol = main_protocol.refresh()
        self.assertTrue(main_protocol.get_model().is_partially_run)
        self.assertTrue(main_protocol.get_process('p0').get_model().is_success)
        self.assertTrue(main_protocol.get_process('p5').get_model().is_draft)

        sub_protocol = sub_protocol.refresh()
        self.assertTrue(sub_protocol.get_model().is_partially_run)
        self.assertTrue(sub_protocol.get_process('p1').get_model().is_success)
        self.assertTrue(sub_protocol.get_process('p2').get_model().is_draft)
        self.assertTrue(sub_protocol.get_process(
            'p_wait').get_model().is_draft)
        self.assertTrue(sub_protocol.get_process('p3').get_model().is_draft)
        self.assertTrue(sub_protocol.get_process('p4').get_model().is_draft)

        # Check that the resource of resetted process is deleted and the other are kept
        self.assertIsNone(ResourceModel.get_by_id(main_resource_to_clear.id))
        self.assertIsNotNone(ResourceModel.get_by_id(sub_resource_to_keep.id))
        self.assertIsNone(ResourceModel.get_by_id(sub_resource_to_clear.id))

        # rerun the scenario and check that it is successfull
        scenario.refresh()
        scenario.run()
        self.assertTrue(scenario.get_model().is_success)
        main_protocol = scenario.get_protocol()
        self.assertTrue(main_protocol.get_model().is_success)

        # Test using the output resource in another scenario and the first process should not be resettable
        # retrieve the main resource
        main_resource: ResourceModel = main_protocol.get_process(
            'p5').get_output_resource_model('robot')

        scenario2 = ScenarioProxy()
        robot_mode = scenario2.get_protocol().add_task(RobotMove, 'robot')
        scenario2.get_protocol().add_resource(
            'source', main_resource.id, robot_mode << 'robot')

        reset_impact = EntityNavigatorService.check_impact_for_process_reset(
            sub_protocol.get_model().id, 'p2')
        self.assertTrue(reset_impact.has_entities)

    def test_run_protocol_process(self):
        scenario = ScenarioProxy()
        i_protocol = scenario.get_protocol()
        protocol_id = i_protocol.get_model().id
        p0 = i_protocol.add_process(RobotCreate, 'p0')
        p1 = i_protocol.add_process(RobotMove, 'p1')
        p2 = i_protocol.add_process(RobotMove, 'p2')
        p3 = i_protocol.add_process(RobotMove, 'p3')
        i_protocol.add_connector(p0 >> 'robot', p1 << 'robot')
        i_protocol.add_connector(p1 >> 'robot', p2 << 'robot')
        i_protocol.add_connector(p2 >> 'robot', p3 << 'robot')

        # Run process p0
        ProtocolService.run_process(protocol_id, 'p0')
        scenario.refresh()

        count = 0
        while count < 30:
            p0.refresh()
            if p0.get_model().is_finished:
                break
            sleep(1)
            count += 1
        p0.refresh()
        p1.refresh()
        self.assertTrue(p0.get_model().is_success)
        self.assertTrue(p1.get_model().is_draft)

        # Test run process p1
        ProtocolService.run_process(protocol_id, 'p1')

        count = 0
        while count < 30:
            p1.refresh()
            if p1.get_model().is_finished:
                break
            sleep(1)
            count += 1

        p1.refresh()
        self.assertTrue(p1.get_model().is_success)

        # Test run process p4 which shoud not be runable
        with self.assertRaises(Exception):
            ProtocolService.run_process(protocol_id, 'p3')

    def test_duplicate_process_to_protocol_id(self):
        protocol_model: ProtocolModel = ProtocolService.create_empty_protocol()

        process_model: ProcessModel = ProtocolService.add_process_to_protocol_id(
            protocol_model.id, RobotMove.get_typing_name()).process

        ProtocolService.duplicate_process_to_protocol_id(
            protocol_model.id, process_model.instance_name)

        protocol_model = protocol_model.refresh()

        duplicated_process = protocol_model.get_process(
            process_model.instance_name + '_1')

        self.assertEqual(len(protocol_model.processes), 2)
        self.assertIsNotNone(duplicated_process)
        self.assertEqual(duplicated_process.get_process_type(), RobotMove)
        self.assertEqual(duplicated_process.to_config_dto().inputs, process_model.to_config_dto().inputs)
        self.assertEqual(duplicated_process.to_config_dto().outputs, process_model.to_config_dto().outputs)

    def test_add_streamlite_community_agent_version_to_protocol(self):
        protocol_model: ProtocolModel = ProtocolService.create_empty_protocol()

        community_agent_version: CommunityAgentVersionDTO = CommunityAgentVersionDTO.from_json(
            {
                'id': '6f12dde5-3fc5-4b83-b5e0-3ab586eda6b2',
                'version': 2,
                'type': 'TASK.gws_core.StreamlitAgent',
                'environment': None,
                'code': '# This is a template for a streamlit agent.\n# This generates an app with one dataframe as input. Then the user can select 2 columns to plot a scatter plot.\n\nimport plotly.express as px\nimport streamlit as st\nfrom pandas import DataFrame\n\n# Your Streamlit app code here\nst.title("App example")\n\n# show a table from file_path which is a csv file full width\nif sources:\n    df: DataFrame = sources[0].get_data()\n\n    # show the dataframe\n    st.dataframe(df)\n\n    # add a select widget with the columns names with no default value\n    # set the selectbox side by side\n    col1, col2 = st.columns(2)\n\n    with col1:\n        x_col = st.selectbox("Select x column", options=df.columns, index=0)\n\n    with col2:\n        y_col = st.selectbox("Select y column", options=df.columns, index=1)\n\n    if x_col and y_col:\n        # Generate a scatter plot with plotly express\n        fig = px.scatter(df, x=x_col, y=y_col)\n        st.plotly_chart(fig)\n',
                'params': {'specs': {}, 'values': {}},
                'input_specs': {'specs': {"source": {"resource_types": [{"typing_name": "RESOURCE.gws_core.Resource", "brick_version": "0.10.0", "human_name": "Resource", "style": {"icon_technical_name": "resource", "icon_type": "MATERIAL_ICON", "background_color": "#c7c8cc", "icon_color": "#000000"}, "short_description": ""}], "human_name": "Resource", "short_description": "", "optional": True, "sub_class": None, "constant": None}}},
                'output_specs': {'specs': {"streamlit_app": {"resource_types": [{"typing_name": "RESOURCE.gws_core.StreamlitResource", "brick_version": "0.10.0", "human_name": "Streamlit App", "style": {"icon_technical_name": "dashboard", "icon_type": "MATERIAL_ICON", "background_color": "#ff4b4b", "icon_color": "#000000"}, "short_description": "Streamlit App"}], "human_name": "Streamlit app", "short_description": "Streamlit App", "optional": False, "sub_class": False, "constant": False}}},
                'config_specs': {},
                'agent': {'id': 'd4816577-94b6-4cc7-a363-52127f4e4525', 'title': 'Test Streamlit', 'latest_publish_version': 2}
            })

        ProtocolService.add_community_agent_version_to_protocol_id(
            protocol_model.id, community_agent_version)

        ProtocolService.add_community_agent_version_to_protocol_id(
            protocol_model.id, community_agent_version)

        protocol_model = protocol_model.refresh()

        streamlit_base_process_name = StreamlitAgent().get_typing_name().split('.')[-1]

        streamlit_process = protocol_model.get_process(streamlit_base_process_name)
        duplicated_streamlit_process = protocol_model.get_process(streamlit_base_process_name + '_1')

        self.assertIsNotNone(streamlit_process)
        self.assertEqual(streamlit_process.get_process_type(), StreamlitAgent)
        self.assertEqual(len(protocol_model.processes), 2)
        self.assertIsNotNone(duplicated_streamlit_process)
        self.assertEqual(streamlit_process.get_name(), 'Test Streamlit')

    def test_add_community_agent_with_multiple_io(self):
        protocol_model: ProtocolModel = ProtocolService.create_empty_protocol()

        first_input = {
            "resource_types":
            [{"typing_name": "RESOURCE.gws_core.Resource", "brick_version": "0.10.0", "human_name": "Resource",
              "style":
              {"icon_technical_name": "resource", "icon_type": "MATERIAL_ICON", "background_color": "#c7c8cc",
               "icon_color": "#000000"},
              "short_description": ""}],
            "human_name": "Resource", "short_description": "", "optional": True, "sub_class": None,
            "constant": None}
        second_input = {
            "resource_types":
            [{"typing_name": "RESOURCE.gws_core.Table", "brick_version": "0.10.0", "human_name": "Table",
              "style":
              {"icon_technical_name": "table", "icon_type": "MATERIAL_ICON", "background_color": "#c7c8cc",
               "icon_color": "#000000"},
              "short_description": ""}],
            "human_name": "Table", "short_description": "", "optional": True, "sub_class": None,
            "constant": None}

        first_output = {
            "resource_types":
            [{"typing_name": "RESOURCE.gws_core.Resource", "brick_version": "0.10.0", "human_name": "Resource",
              "style":
              {"icon_technical_name": "resource", "icon_type": "MATERIAL_ICON", "background_color": "#c7c8cc",
               "icon_color": "#000000"},
              "short_description": ""}],
            "human_name": "Res Resource", "short_description": "", "optional": False, "sub_class": True,
            "constant": False}

        second_output = {
            "resource_types":
            [{"typing_name": "RESOURCE.gws_core.Table", "brick_version": "0.10.0", "human_name": "Table",
              "style":
              {"icon_technical_name": "table", "icon_type": "MATERIAL_ICON", "background_color": "#c7c8cc",
               "icon_color": "#000000"},
              "short_description": ""}],
            "human_name": "Res Table", "short_description": "", "optional": False, "sub_class": True,
            "constant": False}

        community_agent_version: CommunityAgentVersionDTO = CommunityAgentVersionDTO.from_json(
            {
                'id': '6f12dde5-3fc5-4b83-b5e0-3ab586eda6b2',
                'version': 2,
                'type': 'TASK.gws_core.PyAgent',
                'environment': None,
                'code': '# This is a template',
                'params': {'specs': {}, 'values': {}},
                'input_specs': {
                    'specs': {
                        "source": first_input,
                        "table": second_input
                    }
                },
                'output_specs': {
                    'specs': {
                        "target": first_output,
                        "table": second_output
                    }
                },
                'config_specs': {},
                'agent': {'id': 'd4816577-94b6-4cc7-a363-52127f4e4525', 'title': 'Test PyAgent', 'latest_publish_version': 2}
            })

        ProtocolService.add_community_agent_version_to_protocol_id(
            protocol_model.id, community_agent_version)

        protocol_model = protocol_model.refresh()

        base_process_name = PyAgent().get_typing_name().split('.')[-1]
        agent_process = protocol_model.get_process(base_process_name)

        self.assertIsNotNone(agent_process)
        self.assertEqual(agent_process.get_process_type(), PyAgent)
        self.assertEqual(len(protocol_model.processes), 1)
        self.assertEqual(len(agent_process.inputs.ports), 2)
        self.assertEqual(len(agent_process.outputs.ports), 2)
