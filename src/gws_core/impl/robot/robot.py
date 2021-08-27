# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import time
from typing import List

from gws_core.config.config_params import ConfigParams
from gws_core.process.process_io import ProcessIO
from gws_core.resource.resource import Resource
from gws_core.resource.resource_data import ResourceData

from ...process.process import Process
from ...process.process_decorator import ProcessDecorator
from ...process.process_model import ProcessModel
from ...processable.processable_factory import ProcessableFactory
from ...progress_bar.progress_bar import ProgressBar
from ...protocol.protocol import ProcessableSpec, Protocol
from ...protocol.protocol_decorator import ProtocolDecorator
from ...protocol.protocol_model import ProtocolModel
from ...resource.resource_decorator import ResourceDecorator


@ResourceDecorator("Robot")
class Robot(Resource):
    def __init__(self, data: ResourceData = None):
        super().__init__(data)

        if self.data.is_empty():
            self.data.set_values({
                "age": 9,
                "position": [0, 0],
                "weight": 70
            })

    @property
    def age(self) -> int:
        return self.data['age']

    @property
    def position(self) -> List[int]:
        return self.data['position']

    @property
    def weight(self) -> int:
        return self.data['weight']

    def set_position(self, val: List[int]):
        self.data['position'] = val

    def set_weight(self, val: int):
        self.data['weight'] = val

    def set_age(self, val: int):
        self.data['age'] = val


@ResourceDecorator("RobotAddOn")
class RobotAddOn(Resource):
    pass


@ResourceDecorator("MegaRobot")
class MegaRobot(Robot):
    pass


@ProcessDecorator("RobotCreate", human_name="Create robot", short_description="This process creates a robot")
class RobotCreate(Process):
    input_specs = {}  # no required input
    output_specs = {'robot': Robot}
    config_specs = {}

    async def task(self, config: ConfigParams, inputs: ProcessIO, progress_bar: ProgressBar) -> ProcessIO:
        print("Create", flush=True)
        robot: Robot = Robot()

        return {'robot': robot}


@ProcessDecorator("RobotMove", human_name="Move robot",
                  short_description="This process emulates a short moving step of the robot")
class RobotMove(Process):
    input_specs = {'robot': Robot}  # just for testing
    output_specs = {'robot': Robot}
    config_specs = {'moving_step': {"type": float, "default": 0.1, 'description': "The moving step of the robot"}, 'direction': {
        "type": str, "default": "north", "allowed_values": ["north", "south", "east", "west"], 'description': "The moving direction"}}

    async def task(self, config: ConfigParams, inputs: ProcessIO, progress_bar: ProgressBar) -> ProcessIO:
        print(f"Moving {config.get_param('moving_step')}", flush=True)
        robot = Robot()

        pos = inputs['robot'].position.copy()
        direction = config.get_param('direction')
        if direction == "north":
            pos[1] += config.get_param('moving_step')
        elif direction == "south":
            pos[1] -= config.get_param('moving_step')
        elif direction == "west":
            pos[0] -= config.get_param('moving_step')
        elif direction == "east":
            pos[0] += config.get_param('moving_step')

        for i in range(0, 100):
            progress_bar.set_value(i, message=f"Moving iteration {i}")

        robot.set_position(pos)
        robot.set_weight(inputs['robot'].weight)
        return {'robot': robot}


@ProcessDecorator("RobotEat", human_name="Eat process",
                  short_description="This process emulates the meal of the robot before its flight!")
class RobotEat(Process):
    input_specs = {'robot': Robot}
    output_specs = {'robot': Robot}
    config_specs = {
        'food_weight': {"type": float, "default": 3.14}
    }

    async def task(self, config: ConfigParams, inputs: ProcessIO, progress_bar: ProgressBar) -> ProcessIO:
        print(f"Eating {config.get_param('food_weight')}", flush=True)
        robot = Robot()
        robot.set_position(inputs['robot'].position.copy())
        robot.set_weight(inputs['robot'].weight +
                         config.get_param('food_weight'))
        return {'robot': robot}


@ProcessDecorator("RobotWait", human_name="Wait process",
                  short_description="This process emulates the resting time of the robot before its flight!")
class RobotWait(Process):
    input_specs = {'robot': Robot}
    output_specs = {'robot': Robot}
    config_specs = {
        # wait for .5 secs by default
        'waiting_time': {"type": float, "default": 0.5}
    }

    async def task(self, config: ConfigParams, inputs: ProcessIO, progress_bar: ProgressBar) -> ProcessIO:
        print(f"Waiting {config.get_param('waiting_time')}", flush=True)
        robot = Robot()
        robot.set_position(inputs['robot'].position.copy())
        robot.set_weight(inputs['robot'].weight)
        robot.set_age(inputs['robot'].age)
        time.sleep(config.get_param('waiting_time'))
        return {'robot': robot}


@ProcessDecorator("RobotFly", human_name="Fly process",
                  short_description="This process emulates the fly of the robot. It inherites the Move process.")
class RobotFly(RobotMove):
    config_specs = {'moving_step': {"type": float, "default": 1000.0, "unit": "km"}, 'direction': {
        "type": str, "default": "west", "allowed_values": ["north", "south", "east", "west"], 'description': "The flying direction"}}

    async def task(self, config: ConfigParams, inputs: ProcessIO, progress_bar: ProgressBar) -> ProcessIO:
        print("Start flying ...")
        return await super().task(config=config, inputs=inputs, progress_bar=progress_bar)


@ProcessDecorator("RobotAdd")
class RobotAdd(Process):
    input_specs = {'robot': Robot, 'addon': RobotAddOn}
    output_specs = {'mega_robot': MegaRobot}
    config_specs = {}

    async def task(self, config: ConfigParams, inputs: ProcessIO, progress_bar: ProgressBar) -> ProcessIO:
        print("Add robot addon...")
        mega = MegaRobot()
        mega.set_position(inputs['robot'].position.copy())
        mega.set_weight(inputs['robot'].weight)
        return {'mega_robot':  mega}


@ProcessDecorator(unique_name="RobotAddOnCreate", human_name="The travel of `Astro`",
                  short_description="This is the travel of astro composed of several steps")
class RobotAddOnCreate(Process):
    input_specs = {}
    output_specs = {'addon': RobotAddOn}
    config_specs = {}

    async def task(self, config: ConfigParams, inputs: ProcessIO, progress_bar: ProgressBar) -> ProcessIO:
        print("AddOn Create", flush=True)
        return {'addon': RobotAddOn()}


def create_protocol():
    facto: ProcessModel = ProcessableFactory.create_process_model_from_type(
        process_type=RobotCreate)
    move_1: ProcessModel = ProcessableFactory.create_process_model_from_type(
        process_type=RobotMove)
    eat_1: ProcessModel = ProcessableFactory.create_process_model_from_type(
        process_type=RobotEat)
    move_2: ProcessModel = ProcessableFactory.create_process_model_from_type(
        process_type=RobotMove)
    move_3: ProcessModel = ProcessableFactory.create_process_model_from_type(
        process_type=RobotMove)
    eat_2: ProcessModel = ProcessableFactory.create_process_model_from_type(
        process_type=RobotEat)
    wait_1: ProcessModel = ProcessableFactory.create_process_model_from_type(
        process_type=RobotWait)
    fly_1: ProcessModel = ProcessableFactory.create_process_model_from_type(
        process_type=RobotFly)

    proto: ProtocolModel = ProcessableFactory.create_protocol_model_from_data(
        processes={
            'facto': facto,
            'move_1': move_1,
            'eat_1': eat_1,
            'move_2': move_2,
            'move_3': move_3,
            'eat_2': eat_2,
            'fly_1': fly_1,
            'wait_1': wait_1
        },
        connectors=[
            facto >> 'robot' | move_1 << 'robot',
            move_1 >> 'robot' | eat_1 << 'robot',
            eat_1 >> 'robot' | wait_1 << 'robot',
            wait_1 >> 'robot' | move_2 << 'robot',
            move_2 >> 'robot' | move_3 << 'robot',
            eat_1 >> 'robot' | eat_2 << 'robot',
            eat_2 >> 'robot' | fly_1 << 'robot'
        ],
        interfaces={},
        outerfaces={}
    )

    proto.save()

    return proto


@ProtocolDecorator("RobotTravelProto")
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


@ProtocolDecorator("RobotSuperTravelProto", human_name="The super travel of Astro")
class RobotSuperTravelProto(Protocol):
    # config for the eat_3 process
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


@ProtocolDecorator("RobotWorldTravelProto", human_name="The world trip of Astro")
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
