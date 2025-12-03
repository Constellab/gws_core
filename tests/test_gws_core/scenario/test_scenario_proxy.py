from typing import cast

from gws_core import BaseTestCase, ProcessProxy, ProtocolModel, ProtocolProxy, ScenarioProxy, TaskProxy
from gws_core.impl.robot.robot_protocol import RobotSuperTravelProto, RobotTravelProto
from gws_core.impl.robot.robot_resource import Robot
from gws_core.impl.robot.robot_tasks import RobotCreate, RobotMove
from gws_core.protocol.protocol_exception import IOFaceConnectedToTheParentDeleteException
from gws_core.resource.resource_dto import ResourceOrigin
from gws_core.resource.resource_model import ResourceModel
from gws_core.resource.resource_set.resource_set import ResourceSet
from gws_core.resource.resource_set.resource_set_tasks import ResourceStacker


# test_scenario_proxy
class TestScenarioProxy(BaseTestCase):
    def test_scenario_proxy(self):
        scenario: ScenarioProxy = ScenarioProxy()

        protocol: ProtocolProxy = scenario.get_protocol()
        create: ProcessProxy = protocol.add_process(RobotCreate, "create")

        # Verify that the process was created in the DB
        self.assertIsNotNone(create.get_model().id)

        # create manually a sub proto
        sub_proto: ProtocolProxy = protocol.add_empty_protocol("sub_proto")
        sub_move: ProcessProxy = sub_proto.add_process(RobotMove, "sub_move", {"moving_step": 20})
        # test parent of sub_move
        self.assertEqual(sub_move.parent_protocol.instance_name, "sub_proto")

        sub_proto.add_interface("new_robot_i", sub_move.instance_name, "robot")
        sub_proto.add_outerface("new_robot_o", sub_move.instance_name, "robot")

        # Add a RobotTravel protocol
        robot_travel: ProtocolProxy = protocol.add_protocol(RobotTravelProto, "robot_travel")

        # Add main protocol connectors
        protocol.add_connectors(
            [
                (create >> "robot", sub_proto << "new_robot_i"),
                (sub_proto >> "new_robot_o", robot_travel << "travel_int"),
            ]
        )

        # test the get process
        robot_travel_2: ProtocolProxy = protocol.get_process("robot_travel")
        self.assertIsInstance(robot_travel_2, ProtocolProxy)

        scenario.run()
        sub_proto = protocol.get_process("sub_proto")
        sub_move = sub_proto.get_process("sub_move")
        robot_travel = protocol.get_process("robot_travel")

        # Check that the move worked and the config was set
        robot_i: Robot = sub_move.get_input("robot")
        robot_o: Robot = sub_move.get_output("robot")
        self.assertEqual(robot_i.position[0], robot_o.position[0])
        self.assertEqual(robot_i.position[1] + 20, robot_o.position[1])

        # Test the sub proto outerface
        robot_o = sub_move.get_output("robot")
        robot_o2: Robot = sub_proto.get_output("new_robot_o")
        self.assertEqual(robot_o, robot_o2)

        # Test that the RobotTravelProto worked
        robot_o = robot_travel.get_output("travel_out")
        self.assertIsInstance(robot_o, Robot)

        # test that robot_travel has a sub process
        move_1 = robot_travel.get_process("move_1")
        self.assertIsInstance(move_1, TaskProxy)

        # load existing scenario in a new scenario proxy
        scenario_2: ScenarioProxy = ScenarioProxy.from_existing_scenario(scenario.get_model_id())
        protocol_2: ProtocolProxy = scenario_2.get_protocol()
        self.assertEqual(scenario_2.get_model().id, scenario.get_model_id())
        self.assertEqual(protocol_2.get_model().id, protocol.get_model_id())

    def test_scenario_proxy_remove(self):
        scenario: ScenarioProxy = ScenarioProxy(RobotSuperTravelProto)

        super_travel: ProtocolProxy = scenario.get_protocol()
        super_travel_model: ProtocolModel = super_travel.get_model()
        sub_travel: ProtocolProxy = super_travel.get_process("sub_travel")
        move_1: ProcessProxy = sub_travel.get_process("move_1")

        # Try to remove the interface of sub travel, it should raise an exception
        # because the input of sub_travel is connected
        self.assertRaises(IOFaceConnectedToTheParentDeleteException, sub_travel.delete_interface, "travel_int")
        self.assertRaises(IOFaceConnectedToTheParentDeleteException, sub_travel.delete_outerface, "travel_out")

        # Remove interface
        super_travel.delete_interface("super_travel_int")
        self.assertEqual(len(super_travel_model.interfaces), 0)
        self.assertEqual(len(super_travel_model.inputs.ports), 0)

        # Remove outerface
        super_travel.delete_outerface("super_travel_out")
        self.assertEqual(len(super_travel_model.outerfaces), 0)
        self.assertEqual(len(super_travel_model.outputs.ports), 0)

        # Test removing the process
        super_travel.delete_process("sub_travel")
        self.assertRaises(Exception, super_travel.get_process, "sub_travel")
        # Test also that the process of sub_travel was delete form DB
        self.assertRaises(Exception, TaskProxy.get_by_id, move_1.get_model().id)

        # Test info in protocol model
        self._test_super_travel_after_remove(super_travel_model)

        # Verify that the DB was updated
        super_travel_db: ProtocolModel = ProtocolProxy.get_by_id(super_travel_model.id).get_model()
        self._test_super_travel_after_remove(super_travel_db)

    def _test_super_travel_after_remove(self, super_travel_model: ProtocolModel):
        """Method used by the test_scenario_proxy_remove to test the protocol model after removes

        :param protocol_model: [description]
        :type protocol_model: ProtocolModel
        """
        # Test thath the sub process was deleted
        self.assertRaises(Exception, super_travel_model.get_process, "sub_travel")

        # Test that the connectors were deleted
        self.assertEqual(len(super_travel_model.connectors), 0)

        # Test that the interface and input are delete
        self.assertRaises(Exception, super_travel_model.interfaces.__getitem__, "robot")
        self.assertRaises(Exception, super_travel_model.inputs.get_port, "robot")

        # Test that the outerface and output
        self.assertRaises(Exception, super_travel_model.outerfaces.__getitem__, "robot")
        self.assertRaises(Exception, super_travel_model.outputs.get_port, "robot")

    def test_add_resources_to_dynamic_input(self):
        """Test the add_resources_to_dynamic_input method with ResourceStacker task"""
        # Create two robot resources to add as inputs
        robot_1 = Robot.empty()
        robot_1.name = "robot_1"
        robot_1_model = ResourceModel.save_from_resource(robot_1, ResourceOrigin.UPLOADED)

        robot_2 = Robot.empty()
        robot_2.name = "robot_2"
        robot_2_model = ResourceModel.save_from_resource(robot_2, ResourceOrigin.UPLOADED)

        robot_3 = Robot.empty()
        robot_3.name = "robot_3"
        robot_3_model = ResourceModel.save_from_resource(robot_3, ResourceOrigin.UPLOADED)

        # Create scenario with ResourceStacker task that uses dynamic inputs
        scenario: ScenarioProxy = ScenarioProxy()
        protocol: ProtocolProxy = scenario.get_protocol()

        # Add ResourceStacker task
        stacker: ProcessProxy = protocol.add_process(ResourceStacker, "stacker")

        # Use add_resources_to_dynamic_input to add 2 robot resources
        protocol.add_resources_to_process_dynamic_input(
            resource_model_ids=[robot_1_model.id, robot_2_model.id], process_instance_name="stacker"
        )

        # Add the thirs robot later to verify the add works when port already exist
        protocol.add_resources_to_process_dynamic_input(
            resource_model_ids=[robot_3_model.id], process_instance_name="stacker"
        )

        # Run the scenario
        scenario.run()

        # Refresh the stacker to get updated outputs
        stacker.refresh()

        # Get the output resource set
        resource_set: ResourceSet = cast(ResourceSet, stacker.get_output("resource_set"))

        # Verify it has 3 sub resources
        self.assertIsInstance(resource_set, ResourceSet)
        self.assertEqual(len(resource_set.get_resources()), 3)

        # Verify the resources are the ones we added
        resources = resource_set.get_resources()
        resource_names = [res.name for res in resources.values()]
        self.assertIn("robot_1", resource_names)
        self.assertIn("robot_2", resource_names)
        self.assertIn("robot_3", resource_names)
