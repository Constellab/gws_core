# LICENSE
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import time

from gws.settings import Settings
from gws.model import Config, Process, Resource, Model, Protocol
from gws.controller import Controller

class Robot(Resource):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.data = { 
            "age": 9,
            "position": [0,0],
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

class Create(Process):
    input_specs = {}  #no required input
    output_specs = {'robot' : Robot}
    config_specs = {}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.set_title("Robot create")
        self.data["description"] =  "This process creates the Robot."

    async def task(self):
        print("Create", flush=True)
        r = Robot()
        r.set_title("Astro Boy")
        r.data["description"] = "Astro Boy, known in Japan by its original name Mighty Atom (Japanese: 鉄腕アトム, Hepburn: Tetsuwan Atomu), is a Japanese manga series written and illustrated by Osamu Tezuka."
        r.data["more"] = "https://en.wikipedia.org/wiki/Astro_Boy"

        self.output['robot'] = r

class Move(Process):
    input_specs = {'robot' : Robot}  #just for testing
    output_specs = {'robot' : Robot}
    config_specs = {
        'moving_step': {"type": float, "default": 0.1, 'description': "The moving step of the robot"},
        'direction': {"type": str, "default": "north", "allowed_values":["north", "south", "east", "west"], 'description': "The moving direction"}
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.set_title("Move process")
        self.data["description"] =  "This process emulates a short moving step of the robot"

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

        r.set_position(pos)
        r.set_weight(self._input['robot'].weight)
        self.output['robot'] = r

class Eat(Process):
    input_specs = {'robot' : Robot}
    output_specs = {'robot' : Robot}
    config_specs = {
        'food_weight': {"type": float, "default": 3.14}
    }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.set_title("Eat process")
        self.data["description"] = "This process emulates the meal of the robot before its flight!"


    async def task(self):
        print(f"Eating {self.get_param('food_weight')}", flush=True)
        r = Robot()
        r.set_position(self.input['robot'].position.copy())
        r.set_weight(self.input['robot'].weight + self.get_param('food_weight'))
        self.output['robot'] = r

class Wait(Process):
    input_specs = {'robot' : Robot}
    output_specs = {'robot' : Robot}
    config_specs = {
        'waiting_time': {"type": float, "default": 0.5} #wait for .5 secs by default
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.set_title("Wait process")
        self.data["description"] =  "This process emulates the resting time of the robot before its flight!"

    async def task(self):
        print(f"Waiting {self.get_param('waiting_time')}", flush=True)
        r = Robot()
        r.set_position(self.input['robot'].position.copy())
        r.set_weight(self.input['robot'].weight)
        r.set_age(self.input['robot'].age)
        self.output['robot'] = r
        time.sleep(self.get_param('waiting_time'))

class Fly(Move):
    config_specs = {
        'moving_step': {"type": float, "default": 1000.0, "unit": "km"},
        'direction': {"type": str, "default": "west", "allowed_values":["north", "south", "east", "west"], 'description': "The flying direction"}
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.set_title("Fly process")
        self.data["description"] = "This process emulates the fly of the robot. It inherites the Move process."

    async def task(self):
        print(f"Start flying ...")
        await super().task()

class Add(Process):
    input_specs = {'robot' : Robot, 'addon' : RobotAddOn}
    output_specs = {'mega_robot' : MegaRobot}
    config_specs = {}
    
    async def task(self):
        print(f"Add robot addon...")
        mega = MegaRobot()
        mega.set_position(self.input['robot'].position.copy())
        mega.set_weight(self.input['robot'].weight)
        mega.data["addon_uri"] = self.input['addon'].uri
        self.output['mega_robot'] = mega  

class AddOnCreate(Process):
    input_specs = {}
    output_specs = {'addon' : RobotAddOn}
    config_specs = {}
    
    async def task(self):
        print("AddOn Create", flush=True)
        self.output['addon'] = RobotAddOn()
        
def create_protocol():
    facto   = Create()
    move_1  = Move()
    eat_1   = Eat()
    move_2  = Move()
    move_3  = Move()
    eat_2   = Eat()
    wait_1  = Wait()
    fly_1   = Fly()

    proto = Protocol(
        processes = {
            'facto' : facto,  
            'move_1' : move_1, 
            'eat_1' : eat_1, 
            'move_2' : move_2,  
            'move_3' : move_3,  
            'eat_2' : eat_2, 
            'fly_1' : fly_1, 
            'wait_1' : wait_1
        },
        connectors=[
            facto>>'robot'     | move_1<<'robot',
            move_1>>'robot'    | eat_1<<'robot',
            eat_1>>'robot'     | wait_1<<'robot',
            wait_1>>'robot'    | move_2<<'robot',
            move_2>>'robot'    | move_3<<'robot',
            eat_1>>'robot'     | eat_2<<'robot',
            eat_2>>'robot'     | fly_1<<'robot'
        ],
        interfaces = {},
        outerfaces = {}
    )

    proto.set_title("The travel of Astro")
    proto.save()
    
    return proto


def _create_super_travel_protocol():
    move_1  = Move()
    eat_1   = Eat()
    move_2  = Move()
    move_3  = Move()
    eat_2   = Eat()
    wait_1  = Wait()

    add_1 = Add()
    addon_create_1 = AddOnCreate()

    sub_travel = Protocol(
        processes = {
            'move_1' : move_1, 
            'eat_1' : eat_1, 
            'move_2' : move_2,  
            'move_3' : move_3,  
            'eat_2' : eat_2, 
            'wait_1' : wait_1,
            'add_1' : add_1,
            'addon_create_1' : addon_create_1,
        },
        connectors=[
            move_1>>'robot'    | eat_1<<'robot',
            eat_1>>'robot'     | wait_1<<'robot',
            
            addon_create_1>>'addon'  | add_1<<'addon',
            wait_1>>'robot'          | add_1<<'robot',
            add_1>>'mega_robot'      | move_2<<'robot',
            
            move_2>>'robot'    | move_3<<'robot',
            eat_1>>'robot'     | eat_2<<'robot',
        ],
        interfaces = { 'robot' : move_1.in_port('robot') },
        outerfaces = { 'robot' : eat_2.out_port('robot') }
    )
    
    move_4  = Move()
    fly_1  = Fly()
    wait_2 = Wait()
    eat_3 = Eat()
    super_travel = Protocol(
        processes = {
            'move_4' : move_4, 
            'fly_1' : fly_1, 
            'sub_travel': sub_travel,
            'eat_3'  : eat_3,
            'wait_2' : wait_2, 
        },
        connectors=[
            move_4>>'robot'       | sub_travel<<'robot',
            sub_travel>>'robot'  | fly_1<<'robot',
            sub_travel>>'robot'  | eat_3<<'robot',
            fly_1>>'robot'       | wait_2<<'robot'
        ],
        interfaces = { 'robot' : move_4.in_port('robot') },
        outerfaces = { 'robot' : eat_3.out_port('robot') },
    )

    sub_travel.set_title('The mini travel of Astro')
    super_travel.set_title("The super travel of Astro")
    
    sub_travel.save()
    super_travel.save()
    
    return super_travel

def create_nested_protocol():
    super_travel = _create_super_travel_protocol()
    
    facto  = Create()
    fly_1  = Fly()
    wait_1 = Wait()
    
    world_trip = Protocol(
        processes = {
            'facto' : facto, 
            'fly_1' : fly_1, 
            'super_travel': super_travel,
            'wait_2' : wait_1, 
        },
        connectors=[
            facto>>'robot'       | super_travel<<'robot',
            super_travel>>'robot'  | fly_1<<'robot',
            fly_1>>'robot'       | wait_1<<'robot'
        ],
        interfaces = { },
        outerfaces = { }
    )
    
    world_trip.set_title("The world trip of Astro")
    world_trip.save()
    
    return world_trip
