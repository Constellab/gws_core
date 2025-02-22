

from gws_core.model.typing_style import TypingStyle
from gws_core.task.plug.input_task import InputTask
from gws_core.task.plug.output_task import OutputTask

from ...protocol.protocol import ProcessSpec, Protocol
from ...protocol.protocol_decorator import protocol_decorator
from .robot_tasks import (RobotAdd, RobotAddOnCreate, RobotCreate, RobotEat,
                          RobotFly, RobotMove)


@protocol_decorator("RobotSimpleTravel", hide=True,
                    style=TypingStyle.material_icon("smart_toy", background_color="#2b6d57"))
class RobotSimpleTravel(Protocol):

    tasks_count = 7
    resources_count = 5

    def configure_protocol(self) -> None:
        facto: ProcessSpec = self.add_process(RobotCreate, 'facto')
        move_1: ProcessSpec = self.add_process(RobotMove, 'move_1').set_param(
            'moving_step', 2000).set_param('direction', 'west')
        eat_1: ProcessSpec = self.add_process(RobotEat, 'eat_1')
        move_2: ProcessSpec = self.add_process(RobotMove, 'move_2')
        eat_2: ProcessSpec = self.add_process(RobotEat, 'eat_2')

        # define the protocol output
        output_1: ProcessSpec = self.add_process(OutputTask, 'output_1')
        output_2: ProcessSpec = self.add_process(OutputTask, 'output_2')

        self.add_connectors([
            (facto >> 'robot', move_1 << 'robot'),
            (move_1 >> 'robot', eat_1 << 'robot'),
            (eat_1 >> 'robot', move_2 << 'robot'),
            (eat_1 >> 'robot', eat_2 << 'robot'),
            (eat_2 >> 'robot', output_1 << 'resource'),
            (move_2 >> 'robot', output_2 << 'resource'),
        ])


@protocol_decorator("RobotTravelProto", hide=True,
                    style=TypingStyle.material_icon("smart_toy", background_color="#2b6d57"))
class RobotTravelProto(Protocol):

    tasks_count = 7
    resource_count = 7

    def configure_protocol(self) -> None:
        move_1: ProcessSpec = self.add_process(RobotMove, "move_1")
        eat_1: ProcessSpec = self.add_process(RobotEat, "eat_1")
        move_2: ProcessSpec = self.add_process(RobotMove, "move_2")
        move_3: ProcessSpec = self.add_process(RobotMove, "move_3")
        eat_2: ProcessSpec = self.add_process(RobotEat, "eat_2")
        add_1: ProcessSpec = self.add_process(RobotAdd, "add_1")
        addon_create_1: ProcessSpec = self.add_process(
            RobotAddOnCreate, "addon_create_1")

        self.add_connectors([
            (move_1 >> 'robot', eat_1 << 'robot'),

            (addon_create_1 >> 'addon', add_1 << 'addon'),
            (eat_1 >> 'robot', add_1 << 'robot'),
            (add_1 >> 'mega_robot', move_2 << 'robot'),

            (move_2 >> 'robot', move_3 << 'robot'),
            (eat_1 >> 'robot', eat_2 << 'robot'),
        ])

        self.add_interface('travel_int', move_1, 'robot')
        self.add_outerface('travel_out', eat_2, 'robot')


@protocol_decorator("RobotSuperTravelProto", human_name="The super travel of Astro",
                    hide=True, style=TypingStyle.material_icon("smart_toy", background_color="#2b6d57"))
class RobotSuperTravelProto(Protocol):

    tasks_count = 1 + RobotTravelProto.tasks_count
    resource_count = 1 + RobotTravelProto.resource_count

    def configure_protocol(self) -> None:
        sub_travel: ProcessSpec = self.add_process(
            RobotTravelProto, 'sub_travel')
        move_4: ProcessSpec = self.add_process(RobotMove, "move_4")

        self.add_connectors([
            (move_4 >> 'robot', sub_travel << 'travel_int'),
        ])

        self.add_interface('super_travel_int', move_4, 'robot')
        self.add_outerface('super_travel_out', sub_travel, 'travel_out')


@protocol_decorator("RobotWorldTravelProto", human_name="The world trip of Astro",
                    hide=True, style=TypingStyle.material_icon("smart_toy", background_color="#2b6d57"))
class RobotWorldTravelProto(Protocol):

    tasks_count = 3 + RobotSuperTravelProto.tasks_count
    resource_count = 2 + RobotSuperTravelProto.resource_count

    def configure_protocol(self) -> None:

        super_travel: ProcessSpec = self.add_process(
            RobotSuperTravelProto, "super_travel")

        facto: ProcessSpec = self.add_process(RobotCreate, "facto")
        fly_1: ProcessSpec = self.add_process(
            RobotFly, "fly_1").set_param(
            'moving_step', 2000).set_param(
            'direction', 'west')

        # define the protocol output
        output_1: ProcessSpec = self.add_process(OutputTask, 'output_1')

        self.add_connectors([
            (facto >> 'robot', super_travel << 'super_travel_int'),
            (super_travel >> 'super_travel_out', fly_1 << 'robot'),
            (fly_1 >> 'robot', output_1 << 'resource')
        ])


@protocol_decorator("CreateSimpleRobot", hide=True,
                    style=TypingStyle.material_icon("smart_toy", background_color="#2b6d57"))
class CreateSimpleRobot(Protocol):
    def configure_protocol(self) -> None:
        facto: ProcessSpec = self.add_process(RobotCreate, 'facto')

        # define the protocol output
        output_1: ProcessSpec = self.add_process(OutputTask, 'output_1')

        self.add_connectors([
            (facto >> 'robot', output_1 << 'resource'),
        ])


@protocol_decorator("MoveSimpleRobot", hide=True,
                    style=TypingStyle.material_icon("smart_toy", background_color="#2b6d57"))
class MoveSimpleRobot(Protocol):

    def configure_protocol(self) -> None:
        source: ProcessSpec = self.add_process(InputTask, 'source')
        move: ProcessSpec = self.add_process(RobotMove, 'move')

        # define the protocol output
        output_1: ProcessSpec = self.add_process(OutputTask, 'output_1')

        self.add_connectors([
            (source >> 'resource', move << 'robot'),
            (move >> 'robot', output_1 << 'resource'),
        ])
