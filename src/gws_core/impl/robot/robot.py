# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import time

from ...process.process import Process
from ...protocol.protocol import Protocol
from ...resource.resource import Resource


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


class RobotAddOn(Resource):
    pass


class MegaRobot(Robot):
    pass


class RobotCreate(Process):
    input_specs = {}  # no required input
    output_specs = {'robot': Robot}
    config_specs = {}
    title = "Create robot"
    description = "This process creates a robot"

    async def task(self):
        print("Create", flush=True)
        r = Robot()
        #r.set_title("Astro Boy")
        c = r.add_comment("""
            Astro Boy, known in Japan by its original name Mighty Atom (Japanese: 鉄腕アトム, Hepburn: Tetsuwan Atomu), is a Japanese manga series written and illustrated by Osamu Tezuka.
            https://en.wikipedia.org/wiki/Astro_Boy
        """)
        r.add_comment("Reply to my comment", reply_to=c)

        self.output['robot'] = r


class RobotMove(Process):
    input_specs = {'robot': Robot}  # just for testing
    output_specs = {'robot': Robot}
    config_specs = {
        'moving_step': {"type": float, "default": 0.1, 'description': "The moving step of the robot"},
        'direction': {"type": str, "default": "north", "allowed_values": ["north", "south", "east", "west"], 'description': "The moving direction"}
    }
    title = "Move robot"
    description = "This process emulates a short moving step of the robot"

    async def task(self):
        print(f"Moving {self.get_param('moving_step')}", flush=True)
        r = Robot()

        pos = self._input['robot'].position.copy()
        direction = self.get_param('direction')
        if direction == "north":
            pos[1] += self.get_param('moving_step')
        elif direction == "south":
            pos[1] -= self.get_param('moving_step')
        elif direction == "west":
            pos[0] -= self.get_param('moving_step')
        elif direction == "east":
            pos[0] += self.get_param('moving_step')

        for i in range(0, 100):
            self.progress_bar.set_value(i, message=f"Moving iteration {i}")

        r.set_position(pos)
        r.set_weight(self._input['robot'].weight)
        self.output['robot'] = r


class RobotEat(Process):
    input_specs = {'robot': Robot}
    output_specs = {'robot': Robot}
    config_specs = {
        'food_weight': {"type": float, "default": 3.14}
    }
    title = "Eat process"
    description = "This process emulates the meal of the robot before its flight!"

    async def task(self):
        print(f"Eating {self.get_param('food_weight')}", flush=True)
        r = Robot()
        r.set_position(self.input['robot'].position.copy())
        r.set_weight(self.input['robot'].weight +
                     self.get_param('food_weight'))
        self.output['robot'] = r


class RobotWait(Process):
    input_specs = {'robot': Robot}
    output_specs = {'robot': Robot}
    config_specs = {
        # wait for .5 secs by default
        'waiting_time': {"type": float, "default": 0.5}
    }
    title = "Wait process"
    description = "This process emulates the resting time of the robot before its flight!"

    async def task(self):
        print(f"Waiting {self.get_param('waiting_time')}", flush=True)
        r = Robot()
        r.set_position(self.input['robot'].position.copy())
        r.set_weight(self.input['robot'].weight)
        r.set_age(self.input['robot'].age)
        self.output['robot'] = r
        time.sleep(self.get_param('waiting_time'))


class RobotFly(RobotMove):
    config_specs = {
        'moving_step': {"type": float, "default": 1000.0, "unit": "km"},
        'direction': {"type": str, "default": "west", "allowed_values": ["north", "south", "east", "west"], 'description': "The flying direction"}
    }
    title = "Fly process"
    description = "This process emulates the fly of the robot. It inherites the Move process."

    async def task(self):
        print(f"Start flying ...")
        await super().task()


class RobotAdd(Process):
    input_specs = {'robot': Robot, 'addon': RobotAddOn}
    output_specs = {'mega_robot': MegaRobot}
    config_specs = {}

    async def task(self):
        print(f"Add robot addon...")
        mega = MegaRobot()
        mega.set_position(self.input['robot'].position.copy())
        mega.set_weight(self.input['robot'].weight)
        mega.data["addon_uri"] = self.input['addon'].uri
        self.output['mega_robot'] = mega


class RobotAddOnCreate(Process):
    input_specs = {}
    output_specs = {'addon': RobotAddOn}
    config_specs = {}

    async def task(self):
        print("AddOn Create", flush=True)
        self.output['addon'] = RobotAddOn()


def create_protocol():
    facto = RobotCreate()
    move_1 = RobotMove()
    eat_1 = RobotEat()
    move_2 = RobotMove()
    move_3 = RobotMove()
    eat_2 = RobotEat()
    wait_1 = RobotWait()
    fly_1 = RobotFly()

    proto = Protocol(
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

    proto.set_title("The travel of `Astro`")
    proto.set_description("""
        This is the travel of astro composed of several steps
        * move
        * eat
        * ...
    """)
    proto.save()

    return proto


class RobotTravelProto(Protocol):

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, user=user, **kwargs)

        if not self.is_built:
            move_1 = RobotMove()
            eat_1 = RobotEat()
            move_2 = RobotMove()
            move_3 = RobotMove()
            eat_2 = RobotEat()
            wait_1 = RobotWait()
            add_1 = RobotAdd()
            addon_create_1 = RobotAddOnCreate()

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

            self._build(
                processes=processes,
                connectors=connectors,
                interfaces=interfaces,
                outerfaces=outerfaces,
                user=user,
                **kwargs
            )


class RobotSuperTravelProto(Protocol):

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, user=user, **kwargs)

        if not self.is_built:
            sub_travel = RobotTravelProto(user=user)
            sub_travel.save()

            move_4 = RobotMove()
            fly_1 = RobotFly()
            wait_2 = RobotWait()
            eat_3 = RobotEat()

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
            sub_travel.save()

            self._build(
                processes=processes,
                connectors=connectors,
                interfaces=interfaces,
                outerfaces=outerfaces,
                user=user,
                **kwargs
            )

            sub_travel.set_title('The mini travel of Astro')
            self.set_title("The super travel of Astro")


class RobotWorldTravelProto(Protocol):

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, user=user, **kwargs)

        if not self.is_built:
            super_travel = RobotSuperTravelProto(user=user)
            facto = RobotCreate()
            fly_1 = RobotFly()
            wait_1 = RobotWait()

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

            self._build(
                processes=processes,
                connectors=connectors,
                interfaces=interfaces,
                outerfaces=outerfaces,
                user=user,
                **kwargs
            )

            self.set_title("The world trip of Astro")


def _create_super_travel_protocol():
    return RobotSuperTravelProto()


def robot_create_nested_protocol():
    return RobotWorldTravelProto()
