from gws_core import BaseTestCase
from gws_core.impl.robot.robot_tasks import RobotMove
from gws_core.process.process_types import ProcessStatus
from gws_core.protocol.protocol_graph import ProtocolGraph
from gws_core.resource.resource_model import ResourceModel
from gws_core.scenario.scenario_proxy import ScenarioProxy
from gws_core.task.plug.output_task import OutputTask
from gws_core.test.test_helper import TestHelper

from ..protocol_examples import SubProtocolTest


# test_protocol_graph
class TestProtocolGraph(BaseTestCase):
    def test_protocol(self):
        resources_count = ResourceModel.select().count()

        # Build the scenario
        resource_model = TestHelper.save_robot_resource()

        scenario = ScenarioProxy()
        protocol = scenario.get_protocol()

        p0 = protocol.add_process(RobotMove, "p0")
        sub_proto = protocol.add_process(SubProtocolTest, "sub_proto")

        # Input > Move > SubProtocol > Output
        protocol.add_resource("source", resource_model.id, p0 << "robot")
        protocol.add_connector(p0 >> "robot", sub_proto << "robot")
        output_task = protocol.add_output("output", sub_proto >> "robot")
        scenario.run()

        output_model = output_task.refresh().get_input_resource_model(OutputTask.input_name)

        scenario_dto = scenario.refresh().get_model().export_protocol()
        protocol_graph = ProtocolGraph(scenario_dto.data.graph)

        # Test the protocol graph
        self.assertEqual(protocol_graph.get_input_resource_ids(), {resource_model.id})
        self.assertEqual(protocol_graph.get_output_resource_ids(), {output_model.id})
        self.assertEqual(
            protocol_graph.get_input_and_output_resource_ids(), {resource_model.id, output_model.id}
        )

        # check the total number of resources, shoudl be all the resource generated since the start of the test
        new_resources_count = ResourceModel.select().count()
        self.assertEqual(
            len(protocol_graph.get_all_resource_ids()), new_resources_count - resources_count
        )

    def test_get_input_resource_ids_of_draft_tasks(self):
        """Test that draft tasks' input resource IDs are correctly collected."""
        resource_model = TestHelper.save_robot_resource()

        # Build a scenario without running it — all tasks remain in DRAFT status
        scenario = ScenarioProxy()
        protocol = scenario.get_protocol()

        p0 = protocol.add_process(RobotMove, "p0")
        sub_proto = protocol.add_process(SubProtocolTest, "sub_proto")

        protocol.add_resource("source", resource_model.id, p0 << "robot")
        protocol.add_connector(p0 >> "robot", sub_proto << "robot")
        protocol.add_output("output", sub_proto >> "robot")

        scenario_dto = scenario.refresh().get_model().export_protocol()
        protocol_graph = ProtocolGraph(scenario_dto.data.graph)

        # All tasks are DRAFT, so p0's input resource should be collected
        # (p0 receives the input resource on its "robot" input port)
        draft_input_ids = protocol_graph.get_input_resource_ids_of_draft_tasks()
        self.assertIn(resource_model.id, draft_input_ids)

        # Now run the scenario — all tasks become SUCCESS
        scenario.run()
        scenario_dto_after_run = scenario.refresh().get_model().export_protocol()
        protocol_graph_after_run = ProtocolGraph(scenario_dto_after_run.data.graph)

        # After a successful run, no tasks are in DRAFT, so the result should be empty
        draft_input_ids_after_run = protocol_graph_after_run.get_input_resource_ids_of_draft_tasks()
        self.assertEqual(draft_input_ids_after_run, set())

    def test_get_input_resource_ids_of_draft_tasks_partially_run(self):
        """Test draft task input collection on a partially run scenario
        by simulating DRAFT status on specific nodes."""
        resource_model = TestHelper.save_robot_resource()

        scenario = ScenarioProxy()
        protocol = scenario.get_protocol()

        p0 = protocol.add_process(RobotMove, "p0")
        p1 = protocol.add_process(RobotMove, "p1")

        # Input > p0 > p1 > Output
        protocol.add_resource("source", resource_model.id, p0 << "robot")
        protocol.add_connector(p0 >> "robot", p1 << "robot")
        protocol.add_output("output", p1 >> "robot")
        scenario.run()

        scenario_dto = scenario.refresh().get_model().export_protocol()
        graph_dto = scenario_dto.data.graph

        # Simulate a partially run scenario: set p1 back to DRAFT
        graph_dto.nodes["p1"].status = ProcessStatus.DRAFT.value

        protocol_graph = ProtocolGraph(graph_dto)
        draft_input_ids = protocol_graph.get_input_resource_ids_of_draft_tasks()

        # p1 is DRAFT — its input resource (output of p0) should be collected
        p1_input_resource_id = graph_dto.nodes["p1"].inputs.ports["robot"].resource_id
        self.assertIsNotNone(p1_input_resource_id)
        self.assertIn(p1_input_resource_id, draft_input_ids)

        # p0 is SUCCESS — its input resource should NOT be collected
        self.assertNotIn(resource_model.id, draft_input_ids)
