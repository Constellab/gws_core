from ...config.config_params import ConfigParams
from ...protocol.protocol import ProcessableSpec, Protocol
from ...protocol.protocol_decorator import protocol_decorator
from .robot_tasks import (RobotAdd, RobotAddOnCreate, RobotCreate, RobotEat,
                          RobotFly, RobotMove, RobotWait)


@protocol_decorator("RobotSimpleTravel")
class RobotSimpleTravel(Protocol):
    def configure_protocol(self, config_params: ConfigParams) -> None:
        facto: ProcessableSpec = self.add_process(RobotCreate, 'facto')
        move_1: ProcessableSpec = self.add_process(RobotMove, 'move_1')
        eat_1: ProcessableSpec = self.add_process(RobotEat, 'eat_1')
        move_2: ProcessableSpec = self.add_process(RobotMove, 'move_2')
        move_3: ProcessableSpec = self.add_process(RobotMove, 'move_3')
        eat_2: ProcessableSpec = self.add_process(RobotEat, 'eat_2')
        wait_1: ProcessableSpec = self.add_process(RobotWait, 'wait_1')
        fly_1: ProcessableSpec = self.add_process(RobotFly, 'fly_1')

        self.add_connectors([
            (facto >> 'robot', move_1 << 'robot'),
            (move_1 >> 'robot', eat_1 << 'robot'),
            (eat_1 >> 'robot', wait_1 << 'robot'),
            (wait_1 >> 'robot', move_2 << 'robot'),
            (move_2 >> 'robot', move_3 << 'robot'),
            (eat_1 >> 'robot', eat_2 << 'robot'),
            (eat_2 >> 'robot', fly_1 << 'robot')
        ])


@protocol_decorator("RobotTravelProto")
class RobotTravelProto(Protocol):

    def configure_protocol(self, config_params: ConfigParams) -> None:
        move_1: ProcessableSpec = self.add_process(RobotMove, "move_1")
        eat_1: ProcessableSpec = self.add_process(RobotEat, "eat_1")
        move_2: ProcessableSpec = self.add_process(RobotMove, "move_2")
        move_3: ProcessableSpec = self.add_process(RobotMove, "move_3")
        eat_2: ProcessableSpec = self.add_process(RobotEat, "eat_2")
        wait_1: ProcessableSpec = self.add_process(RobotWait, "wait_1")
        add_1: ProcessableSpec = self.add_process(RobotAdd, "add_1")
        addon_create_1: ProcessableSpec = self.add_process(RobotAddOnCreate, "addon_create_1")

        self.add_connectors([
            (move_1 >> 'robot', eat_1 << 'robot'),
            (eat_1 >> 'robot', wait_1 << 'robot'),

            (addon_create_1 >> 'addon', add_1 << 'addon'),
            (wait_1 >> 'robot', add_1 << 'robot'),
            (add_1 >> 'mega_robot', move_2 << 'robot'),

            (move_2 >> 'robot', move_3 << 'robot'),
            (eat_1 >> 'robot', eat_2 << 'robot'),
        ])

        self.add_interface('robot', move_1, 'robot')
        self.add_outerface('robot', eat_2, 'robot')


@protocol_decorator("RobotSuperTravelProto", human_name="The super travel of Astro")
class RobotSuperTravelProto(Protocol):
    # config for the eat_3 task
    config_specs = {'third_eat': {"type": float, "default": 3.14}}

    def configure_protocol(self, config_params: ConfigParams) -> None:
        sub_travel: ProcessableSpec = self.add_process(RobotTravelProto, 'sub_travel')

        move_4: ProcessableSpec = self.add_process(RobotMove, "move_4")
        fly_1: ProcessableSpec = self.add_process(RobotFly, "fly_1")
        wait_2: ProcessableSpec = self.add_process(RobotWait, "wait_2")
        eat_3: ProcessableSpec = self.add_process(
            RobotEat, "eat_3").configure(
            'food_weight', config_params['third_eat'])

        self.add_connectors([
            (move_4 >> 'robot', sub_travel << 'robot'),
            (sub_travel >> 'robot', fly_1 << 'robot'),
            (sub_travel >> 'robot', eat_3 << 'robot'),
            (fly_1 >> 'robot', wait_2 << 'robot')
        ])

        self.add_interface('robot', move_4, 'robot')
        self.add_outerface('robot', eat_3, 'robot')


@protocol_decorator("RobotWorldTravelProto", human_name="The world trip of Astro")
class RobotWorldTravelProto(Protocol):

    def configure_protocol(self, config_params: ConfigParams) -> None:

        super_travel: ProcessableSpec = self.add_process(RobotSuperTravelProto, "super_travel")\
            .configure('third_eat', 10)

        facto: ProcessableSpec = self.add_process(RobotCreate, "facto")
        fly_1: ProcessableSpec = self.add_process(RobotFly, "fly_1")\
            .configure('moving_step', 2000).configure('direction', 'west')
        wait_1: ProcessableSpec = self.add_process(RobotWait, "wait_1")

        self.add_connectors([
            (facto >> 'robot', super_travel << 'robot'),
            (super_travel >> 'robot', fly_1 << 'robot'),
            (fly_1 >> 'robot', wait_1 << 'robot')
        ])
