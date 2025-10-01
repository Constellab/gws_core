

from gws_core import BaseTestCase
from gws_core.impl.robot.robot_tasks import RobotMove
from gws_core.protocol.protocol_graph import ProtocolGraph
from gws_core.resource.resource_model import ResourceModel
from gws_core.scenario.scenario_proxy import ScenarioProxy
from gws_core.task.plug.output_task import OutputTask
from gws_core.test.test_helper import TestHelper

from ..protocol_examples import TestSubProtocol


# test_protocol_graph
class TestProtocolGraph(BaseTestCase):

    def test_protocol(self):

        resources_count = ResourceModel.select().count()

        # Build the scenario
        resource_model = TestHelper.save_robot_resource()

        scenario = ScenarioProxy()
        protocol = scenario.get_protocol()

        p0 = protocol.add_process(RobotMove, 'p0')
        sub_proto = protocol.add_process(TestSubProtocol, 'sub_proto')

        # Input > Move > SubProtocol > Output
        protocol.add_resource('source', resource_model.id, p0 << 'robot')
        protocol.add_connector(p0 >> 'robot', sub_proto << 'robot')
        output_task = protocol.add_output('output', sub_proto >> 'robot')
        scenario.run()

        output_model = output_task.refresh().get_input_resource_model(OutputTask.input_name)

        scenario_dto = scenario.refresh().get_model().export_protocol()
        protocol_graph = ProtocolGraph(scenario_dto.data.graph)

        # Test the protocol graph
        self.assertEqual(protocol_graph.get_input_resource_ids(), {resource_model.id})
        self.assertEqual(protocol_graph.get_output_resource_ids(), {output_model.id})
        self.assertEqual(protocol_graph.get_input_and_output_resource_ids(), {resource_model.id, output_model.id})

        # check the total number of resources, shoudl be all the resource generated since the start of the test
        new_resources_count = ResourceModel.select().count()
        self.assertEqual(len(protocol_graph.get_all_resource_ids()), new_resources_count - resources_count)
