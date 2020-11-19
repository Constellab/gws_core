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
            "position": 0,
            "weight": 70
        }
    
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

class Create(Process):
    input_specs = {}
    output_specs = {'robot' : Robot}
    config_specs = {}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.set_title("Robot factory")
        self.set_data_value("description", "This process creates the Robot. It is designed by Dr. Tenma.")

    def task(self):
        print("Create", flush=True)
        p = Robot()
        p.set_title("Astro Boy")
        p.set_data_value("description", "Astro Boy, known in Japan by its original name Mighty Atom (Japanese: 鉄腕アトム, Hepburn: Tetsuwan Atomu), is a Japanese manga series written and illustrated by Osamu Tezuka.")
        p.set_data_value("more", "https://en.wikipedia.org/wiki/Astro_Boy")

        self.output['robot'] = p

class Move(Process):
    input_specs = {'robot' : Robot}
    output_specs = {'robot' : Robot}
    config_specs = {
        'moving_step': {"type": float, "default": 0.1}
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.set_title("Move process")
        self.set_data_value("description", "This process emulate a short moving step of the robot")

    def task(self):
        print(f"Moving {self.get_param('moving_step')}", flush=True)
        p = Robot()
        p.set_position(self._input['robot'].position + self.get_param('moving_step'))
        p.set_weight(self._input['robot'].weight)
        self.output['robot'] = p

class Eat(Process):
    input_specs = {'robot' : Robot}
    output_specs = {'robot' : Robot}
    config_specs = {
        'food_weight': {"type": float, "default": 3.14}
    }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.set_title("Eat process")
        self.set_data_value("description", "This process emulates the meal of the robot before its flight!")


    def task(self):
        print(f"Eating {self.get_param('food_weight')}", flush=True)
        p = Robot()
        p.set_position(self.input['robot'].position)
        p.set_weight(self.input['robot'].weight + self.get_param('food_weight'))
        self.output['robot'] = p

class Wait(Process):
    input_specs = {'robot' : Robot}
    output_specs = {'robot' : Robot}
    config_specs = {
        'waiting_time': {"type": float, "default": 0.5} #wait for .5 secs by default
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.set_title("Wait process")
        self.set_data_value("description", "This process emulates the resting time of the robot before its flight!")

    def task(self):
        print(f"Waiting {self.get_param('waiting_time')}", flush=True)
        p = Robot()
        p.set_position(self.input['robot'].position)
        p.set_weight(self.input['robot'].weight)
        self.output['robot'] = p  
        time.sleep(self.get_param('waiting_time'))

class Fly(Move):
    config_specs = {
        'moving_step': {"type": float, "default": 1E9}
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.set_title("Fly process")
        self.set_data_value("description", "This process emulates the fly of the robot. It inherites the Move process.")

    def task(self):
        print(f"Start flying ...")
        super().task()

def create_protocol():
    p0 = Create()
    p1 = Move()
    p2 = Eat()
    p3 = Move()
    p4 = Move()
    p5 = Eat()
    p_wait = Wait()
    p6 = Fly()

    proto = Protocol(
        processes = {
            'p0' : p0,  
            'p1' : p1, 
            'p2' : p2, 
            'p3' : p3,  
            'p4' : p4,  
            'p5' : p5, 
            'Fly' : p6, 
            'p_wait' : p_wait
        },
        connectors=[
            p0>>'robot'        | p1<<'robot',
            p1>>'robot'        | p2<<'robot',
            p2>>'robot'        | p_wait<<'robot',
            p_wait>>'robot'    | p3<<'robot',
            p3>>'robot'        | p4<<'robot',
            p2>>'robot'        | p5<<'robot',
            p5>>'robot'        | p6<<'robot'
        ],
        interfaces = {},
        outerfaces = {}
    )

    proto.title = "Specification of the journey of Astro Boy"
    return proto