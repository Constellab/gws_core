import time
from typing import Optional

from ...config.config_params import ConfigParams
from ...impl.robot.robot_resource import (MegaRobot, Robot, RobotAddOn,
                                          RobotFood)
from ...process.process import Process
from ...process.process_decorator import ProcessDecorator
from ...process.process_io import ProcessInputs, ProcessOutputs
from ...progress_bar.progress_bar import ProgressBar


@ProcessDecorator("RobotCreate", human_name="Create robot", short_description="This process creates a robot")
class RobotCreate(Process):
    input_specs = {}  # no required input
    output_specs = {'robot': Robot}
    config_specs = {}

    async def task(self, config: ConfigParams, inputs: ProcessInputs, progress_bar: ProgressBar) -> ProcessOutputs:
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

    async def task(self, config: ConfigParams, inputs: ProcessInputs, progress_bar: ProgressBar) -> ProcessOutputs:
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
    input_specs = {'robot': Robot, 'food': Optional[RobotFood]}
    output_specs = {'robot': Robot}
    config_specs = {
        'food_weight': {"type": float, "default": 3.14}
    }

    async def task(self, config: ConfigParams, inputs: ProcessInputs, progress_bar: ProgressBar) -> ProcessOutputs:
        robot = Robot()
        robot.set_position(inputs['robot'].position.copy())

        multiplicator: int = 1
        if inputs.has_resource('food'):
            food: RobotFood = inputs['food']
            multiplicator = food.multiplicator

        print(f"Eating {config.get_param('food_weight')} with multiplicator : {multiplicator}", flush=True)
        robot.set_weight(inputs['robot'].weight +
                         (config.get_param('food_weight') * multiplicator))
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

    async def task(self, config: ConfigParams, inputs: ProcessInputs, progress_bar: ProgressBar) -> ProcessOutputs:
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

    async def task(self, config: ConfigParams, inputs: ProcessInputs, progress_bar: ProgressBar) -> ProcessOutputs:
        print("Start flying ...")
        return await super().task(config=config, inputs=inputs, progress_bar=progress_bar)


@ProcessDecorator("RobotAdd")
class RobotAdd(Process):
    input_specs = {'robot': Robot, 'addon': RobotAddOn}
    output_specs = {'mega_robot': MegaRobot}
    config_specs = {}

    async def task(self, config: ConfigParams, inputs: ProcessInputs, progress_bar: ProgressBar) -> ProcessOutputs:
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

    async def task(self, config: ConfigParams, inputs: ProcessInputs, progress_bar: ProgressBar) -> ProcessOutputs:
        print("AddOn Create", flush=True)
        return {'addon': RobotAddOn()}
