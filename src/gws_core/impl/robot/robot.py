# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import time

from ...config.config import Config
from ...io.io import Input, Output
from ...process.process import Process
from ...process.process_decorator import ProcessDecorator
from ...process.process_model import ProcessModel
from ...process.processable_factory import ProcessableFactory
from ...progress_bar.progress_bar import ProgressBar
from ...protocol.protocol import Protocol, ProtocolCreateConfig
from ...protocol.protocol_decorator import ProtocolDecorator
from ...protocol.protocol_model import ProtocolModel
from ...resource.resource import Resource
from ...resource.resource_decorator import ResourceDecorator


@ResourceDecorator("Robot")
class Robot(Resource):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if not self.id:
            self.data = {
                "age": 9,
                "position": [0, 0],
                "weight": 70
            }

    @property
    def age(self):
        return self.data['age']

    @property
    def position(self):
        return self.data['position']

    @property
    def weight(self):
        return self.data['weight']

    def set_position(self, val):
        self.data['position'] = val

    def set_weight(self, val):
        self.data['weight'] = val

    def set_age(self, val):
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

    async def task(self, config: Config, inputs: Input, outputs: Output, progress_bar: ProgressBar) -> None:
        print("Create", flush=True)
        r = Robot()
        # r.set_title("Astro Boy")
        c = r.add_comment("""
            Astro Boy, known in Japan by its original name Mighty Atom (Japanese: 鉄腕アトム, Hepburn: Tetsuwan Atomu), is a Japanese manga series written and illustrated by Osamu Tezuka.
            https://en.wikipedia.org/wiki/Astro_Boy
        """)
        r.add_comment("Reply to my comment", reply_to=c)

        outputs['robot'] = r


@ProcessDecorator("RobotMove", human_name="Move robot", short_description="This process emulates a short moving step of the robot")
class RobotMove(Process):
    input_specs = {'robot': Robot}  # just for testing
    output_specs = {'robot': Robot}
    config_specs = {
        'moving_step': {"type": float, "default": 0.1, 'description': "The moving step of the robot"},
        'direction': {"type": str, "default": "north", "allowed_values": ["north", "south", "east", "west"], 'description': "The moving direction"}
    }

    async def task(self, config: Config, inputs: Input, outputs: Output, progress_bar: ProgressBar) -> None:
        print(f"Moving {config.get_param('moving_step')}", flush=True)
        r = Robot()

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

        r.set_position(pos)
        r.set_weight(inputs['robot'].weight)
        outputs['robot'] = r


@ProcessDecorator("RobotEat", human_name="Eat process", short_description="This process emulates the meal of the robot before its flight!")
class RobotEat(Process):
    input_specs = {'robot': Robot}
    output_specs = {'robot': Robot}
    config_specs = {
        'food_weight': {"type": float, "default": 3.14}
    }

    async def task(self, config: Config, inputs: Input, outputs: Output, progress_bar: ProgressBar) -> None:
        print(f"Eating {config.get_param('food_weight')}", flush=True)
        r = Robot()
        r.set_position(inputs['robot'].position.copy())
        r.set_weight(inputs['robot'].weight +
                     config.get_param('food_weight'))
        outputs['robot'] = r


@ProcessDecorator("RobotWait", human_name="Wait process", short_description="This process emulates the resting time of the robot before its flight!")
class RobotWait(Process):
    input_specs = {'robot': Robot}
    output_specs = {'robot': Robot}
    config_specs = {
        # wait for .5 secs by default
        'waiting_time': {"type": float, "default": 0.5}
    }

    async def task(self, config: Config, inputs: Input, outputs: Output, progress_bar: ProgressBar) -> None:
        print(f"Waiting {config.get_param('waiting_time')}", flush=True)
        r = Robot()
        r.set_position(inputs['robot'].position.copy())
        r.set_weight(inputs['robot'].weight)
        r.set_age(inputs['robot'].age)
        outputs['robot'] = r
        time.sleep(config.get_param('waiting_time'))


@ProcessDecorator("RobotFly", human_name="Fly process", short_description="This process emulates the fly of the robot. It inherites the Move process.")
class RobotFly(RobotMove):
    config_specs = {
        'moving_step': {"type": float, "default": 1000.0, "unit": "km"},
        'direction': {"type": str, "default": "west", "allowed_values": ["north", "south", "east", "west"], 'description': "The flying direction"}
    }

    async def task(self, config: Config, inputs: Input, outputs: Output, progress_bar: ProgressBar) -> None:
        print("Start flying ...")
        await super().task(config=config, inputs=inputs, outputs=outputs, progress_bar=progress_bar)


@ProcessDecorator("RobotAdd")
class RobotAdd(Process):
    input_specs = {'robot': Robot, 'addon': RobotAddOn}
    output_specs = {'mega_robot': MegaRobot}
    config_specs = {}

    async def task(self, config: Config, inputs: Input, outputs: Output, progress_bar: ProgressBar) -> None:
        print("Add robot addon...")
        mega = MegaRobot()
        mega.set_position(inputs['robot'].position.copy())
        mega.set_weight(inputs['robot'].weight)
        mega.data["addon_uri"] = inputs['addon'].uri
        outputs['mega_robot'] = mega


@ProcessDecorator(unique_name="RobotAddOnCreate", human_name="The travel of `Astro`", short_description="This is the travel of astro composed of several steps")
class RobotAddOnCreate(Process):
    input_specs = {}
    output_specs = {'addon': RobotAddOn}
    config_specs = {}

    async def task(self, config: Config, inputs: Input, outputs: Output, progress_bar: ProgressBar) -> None:
        print("AddOn Create", flush=True)
        outputs['addon'] = RobotAddOn()


def create_protocol():
    facto: ProcessModel = ProcessableFactory.create_process_from_type(
        process_type=RobotCreate)
    move_1: ProcessModel = ProcessableFactory.create_process_from_type(
        process_type=RobotMove)
    eat_1: ProcessModel = ProcessableFactory.create_process_from_type(
        process_type=RobotEat)
    move_2: ProcessModel = ProcessableFactory.create_process_from_type(
        process_type=RobotMove)
    move_3: ProcessModel = ProcessableFactory.create_process_from_type(
        process_type=RobotMove)
    eat_2: ProcessModel = ProcessableFactory.create_process_from_type(
        process_type=RobotEat)
    wait_1: ProcessModel = ProcessableFactory.create_process_from_type(
        process_type=RobotWait)
    fly_1: ProcessModel = ProcessableFactory.create_process_from_type(
        process_type=RobotFly)

    proto: ProtocolModel = ProcessableFactory.create_protocol_from_data(
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

    def get_create_config(self) -> ProtocolCreateConfig:
        move_1: ProcessModel = ProcessableFactory.create_process_from_type(
            process_type=RobotMove)
        eat_1: ProcessModel = ProcessableFactory.create_process_from_type(
            process_type=RobotEat)
        move_2: ProcessModel = ProcessableFactory.create_process_from_type(
            process_type=RobotMove)
        move_3: ProcessModel = ProcessableFactory.create_process_from_type(
            process_type=RobotMove)
        eat_2: ProcessModel = ProcessableFactory.create_process_from_type(
            process_type=RobotEat)
        wait_1: ProcessModel = ProcessableFactory.create_process_from_type(
            process_type=RobotWait)
        add_1: ProcessModel = ProcessableFactory.create_process_from_type(
            process_type=RobotAdd)
        addon_create_1: ProcessModel = ProcessableFactory.create_process_from_type(
            process_type=RobotAddOnCreate)

        processes = {
            'move_1': move_1,
            'eat_1': eat_1,
            'move_2': move_2,
            'move_3': move_3,
            'eat_2': eat_2,
            'wait_1': wait_1,
            'add_1': add_1,
            'addon_create_1': addon_create_1
        }

        connectors = [
            move_1 >> 'robot' | eat_1 << 'robot',
            eat_1 >> 'robot' | wait_1 << 'robot',

            addon_create_1 >> 'addon' | add_1 << 'addon',
            wait_1 >> 'robot' | add_1 << 'robot',
            add_1 >> 'mega_robot' | move_2 << 'robot',

            move_2 >> 'robot' | move_3 << 'robot',
            eat_1 >> 'robot' | eat_2 << 'robot',
        ]

        interfaces = {'robot': move_1.in_port('robot')}
        outerfaces = {'robot': eat_2.out_port('robot')}

        return {
            "processes": processes,
            "connectors": connectors,
            "interfaces": interfaces,
            "outerfaces": outerfaces,
        }


@ProtocolDecorator("RobotSuperTravelProto", human_name="The super travel of Astro")
class RobotSuperTravelProto(Protocol):

    def get_create_config(self) -> ProtocolCreateConfig:
        sub_travel: ProtocolModel = ProcessableFactory.create_protocol_from_type(
            RobotTravelProto)

        move_4: ProcessModel = ProcessableFactory.create_process_from_type(
            process_type=RobotMove)
        fly_1: ProcessModel = ProcessableFactory.create_process_from_type(
            process_type=RobotFly)
        wait_2: ProcessModel = ProcessableFactory.create_process_from_type(
            process_type=RobotWait)
        eat_3: ProcessModel = ProcessableFactory.create_process_from_type(
            process_type=RobotEat)

        processes = {
            'move_4': move_4,
            'fly_1': fly_1,
            'sub_travel': sub_travel,
            'eat_3': eat_3,
            'wait_2': wait_2,
        }

        connectors = [
            move_4 >> 'robot' | sub_travel << 'robot',
            sub_travel >> 'robot' | fly_1 << 'robot',
            sub_travel >> 'robot' | eat_3 << 'robot',
            fly_1 >> 'robot' | wait_2 << 'robot'
        ]

        interfaces = {'robot': move_4.in_port('robot')}
        outerfaces = {'robot': eat_3.out_port('robot')}

        return {
            "processes": processes,
            "connectors": connectors,
            "interfaces": interfaces,
            "outerfaces": outerfaces,
        }


@ProtocolDecorator("RobotWorldTravelProto", human_name="The world trip of Astro")
class RobotWorldTravelProto(Protocol):

    def get_create_config(self) -> ProtocolCreateConfig:

        super_travel: ProtocolModel = ProcessableFactory.create_protocol_from_type(
            RobotSuperTravelProto)

        facto: ProcessModel = ProcessableFactory.create_process_from_type(
            process_type=RobotCreate)
        fly_1: ProcessModel = ProcessableFactory.create_process_from_type(
            process_type=RobotFly)
        wait_1: ProcessModel = ProcessableFactory.create_process_from_type(
            process_type=RobotWait)

        processes = {
            'facto': facto,
            'fly_1': fly_1,
            'super_travel': super_travel,
            'wait_2': wait_1,
        }

        connectors = [
            facto >> 'robot' | super_travel << 'robot',
            super_travel >> 'robot' | fly_1 << 'robot',
            fly_1 >> 'robot' | wait_1 << 'robot'
        ]

        interfaces = {}
        outerfaces = {}

        return {
            "processes": processes,
            "connectors": connectors,
            "interfaces": interfaces,
            "outerfaces": outerfaces,
        }
