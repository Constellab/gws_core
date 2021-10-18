from gws_core import (BaseTestCase, IExperiment, IProcess, IProtocol, ITask,
                      ProtocolModel, Robot, RobotCreate, RobotMove,
                      RobotSuperTravelProto, RobotTravelProto)


class TestIExperiment(BaseTestCase):

    async def test_iexperiment(self):

        experiment: IExperiment = IExperiment()

        protocol: IProtocol = experiment.get_protocol()
        create: IProcess = protocol.add_process(RobotCreate, 'create')

        # Verify that the process was created in the DB
        self.assertIsNotNone(create._process_model.id)

        # create manually a sub proto
        sub_proto: IProtocol = protocol.add_empty_protocol('sub_proto')
        sub_move: IProcess = sub_proto.add_process(RobotMove, 'sub_move', {'moving_step': 20})
        # test parent of sub_move
        self.assertEqual(sub_move.parent_protocol.instance_name, 'sub_proto')

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
        self.assertIsInstance(robot_travel_2, IProtocol)

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
        self.assertIsInstance(move_1, ITask)

    def test_iexperiment_remove(self):
        experiment: IExperiment = IExperiment(RobotSuperTravelProto)

        super_travel: IProtocol = experiment.get_protocol()
        sub_travel: IProtocol = super_travel.get_process('sub_travel')
        move_1: IProcess = sub_travel.get_process('move_1')

        # Test removing the process
        super_travel.delete_process('sub_travel')
        self.assertRaises(Exception, super_travel.get_process, 'sub_travel')
        # Test also that the process of sub_travel was delete form DB
        self.assertRaises(Exception, ITask.get_by_uri, move_1._process_model.uri)

        # Remove interface
        super_travel.delete_interface('robot')

        # Remove outerface
        super_travel.delete_outerface('robot')

        # Test info in protocol model
        super_travel_model: ProtocolModel = super_travel._protocol_model
        self._test_super_travel_after_remove(super_travel_model)

        # Verify that the DB was updated
        super_travel_db: ProtocolModel = IProtocol.get_by_uri(super_travel_model.uri)._protocol_model
        self._test_super_travel_after_remove(super_travel_db)

    def _test_super_travel_after_remove(self, super_travel_model: ProtocolModel):
        """Method used by the test_iexperiment_remove to test the protocol model after removes

        :param protocol_model: [description]
        :type protocol_model: ProtocolModel
        """
        # Test thath the sub process was deleted
        self.assertRaises(Exception, super_travel_model.get_process, 'sub_travel')

        # Test that the connectors were deleted
        self.assertEqual(len(super_travel_model.connectors), 1)

        # Test that the interface and input are delete
        self.assertRaises(Exception, super_travel_model.interfaces.__getitem__, 'robot')
        self.assertRaises(Exception, super_travel_model.inputs.get_port, 'robot')

        # Test that the outerface and output
        self.assertRaises(Exception, super_travel_model.outerfaces.__getitem__, 'robot')
        self.assertRaises(Exception, super_travel_model.outputs.get_port, 'robot')
