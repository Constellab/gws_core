

from gws_core import BaseTestCase, ScenarioProxy
from gws_core.impl.robot.robot_tasks import RobotCreate, RobotMove
from gws_core.protocol.protocol_layout import (ProcessLayoutDTO,
                                               ProtocolLayout,
                                               ProtocolLayoutDTO)
from gws_core.protocol.protocol_model import ProtocolModel
from gws_core.protocol.protocol_service import ProtocolService


# test_protocol_layout
class TestProtocolLayout(BaseTestCase):

    def test_protocol_layout(self):
        scenario = ScenarioProxy()

        i_protocol = scenario.get_protocol()

        robot_create = i_protocol.add_process(RobotCreate, 'robot_create')
        robot_move = i_protocol.add_process(RobotMove, 'robot_move')

        i_protocol.add_connector(robot_create >> 'robot', robot_move << 'robot')

        protocol_model: ProtocolModel = i_protocol._process_model

        # add layout for create robot process
        ProtocolService.save_process_layout(protocol_model.id, 'robot_create', ProcessLayoutDTO(x=10, y=10))
        protocol_model = protocol_model.refresh()
        layout: ProtocolLayout = protocol_model.layout
        self.assert_json(layout.get_process('robot_create').to_json_dict(), {'x': 10, 'y': 10})

        # define ans save a layout
        dict_layout = ProtocolLayoutDTO(
            process_layouts={
                'robot_create': ProcessLayoutDTO(x=0, y=0),
                'robot_move': ProcessLayoutDTO(x=100, y=100)
            },
            interface_layouts={},
            outerface_layouts={}
        )
        # save a complete layout
        ProtocolService.save_layout(protocol_model.id, dict_layout)

        protocol_model = protocol_model.refresh()

        layout = protocol_model.layout
        self.assertIsInstance(layout, ProtocolLayout)
        self.assert_json(layout.process_layouts, dict_layout.process_layouts)

        # remove the process and check that the layout is updated
        protocol_model.remove_process('robot_create')
        self.assertIsNone(layout.get_process('robot_create'))
