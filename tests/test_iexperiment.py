from gws_core import (IExperiment, IProcess, IProtocol, Robot, RobotCreate,
                      RobotMove, RobotTravelProto)
from gws_core.core.test.base_test_case import BaseTestCase


class TestIExperiment(BaseTestCase):

    async def test_iexperiment(self):

        experiment: IExperiment = IExperiment()

        protocol: IProtocol = experiment.get_protocol()
        create: IProcess = protocol.add_process(RobotCreate, 'create')

        # create manually a sub proto
        sub_proto: IProtocol = protocol.add_empty_protocol('sub_proto')
        sub_move: IProcess = sub_proto.add_process(RobotMove, 'sub_move', {'moving_step': 20})
        sub_proto.add_interface('robot_i', sub_move, 'robot')
        sub_proto.add_outerface('robot_o', sub_move, 'robot')

        # Add a RobotTravel protocol
        robot_travel: IProtocol = protocol.add_protocol(RobotTravelProto, 'robot_travel')

        # Add main protocol connectors
        protocol.add_connectors([
            (create >> 'robot', sub_proto << 'robot_i'),
            (sub_proto >> 'robot_o', robot_travel << 'robot')
        ])

        # test the get process
        robot_travel_2: IProtocol = protocol.get_process('robot_travel')
        self.assertIsNotNone(robot_travel_2)

        await experiment.run()

        # Check that the move worked and the config was set
        robot_i: Robot = sub_move.get_input('robot')
        robot_o: Robot = sub_move.get_output('robot')
        self.assertEqual(robot_i.position[0], robot_o.position[0])
        self.assertEqual(robot_i.position[1] + 20, robot_o.position[1])

        # Test the sub proto outerface
        robot_o = sub_move.get_output('robot')
        robot_o2: Robot = sub_proto.get_output('robot_o')
        self.assertEqual(robot_o, robot_o2)

        # Test that the RobotTravelProto worked
        robot_o = robot_travel.get_output('robot')
        self.assertIsInstance(robot_o, Robot)

        # test that robot_travel has a sub process
        move_1 = robot_travel.get_process('move_1')
        self.assertIsNotNone(move_1)
