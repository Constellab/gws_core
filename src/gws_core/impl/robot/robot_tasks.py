import time
from typing import Optional

from gws_core.config.param_spec import FloatParam, StrParam

from ...config.config_types import ConfigValues
from ...impl.robot.robot_resource import (MegaRobot, Robot, RobotAddOn,
                                          RobotFood)
from ...task.task import Task
from ...task.task_decorator import task_decorator
from ...task.task_io import TaskInputs, TaskOutputs


@task_decorator("RobotCreate", human_name="Create robot", short_description="This task creates a robot")
class RobotCreate(Task):
    input_specs = {}  # no required input
    output_specs = {'robot': Robot}
    config_specs = {}

    async def run(self, config: ConfigValues, inputs: TaskInputs) -> TaskOutputs:
        print("Create", flush=True)
        robot: Robot = Robot.empty()

        return {'robot': robot}


@task_decorator("RobotMove", human_name="Move robot",
                short_description="This task emulates a short moving step of the robot")
class RobotMove(Task):
    input_specs = {'robot': Robot}  # just for testing
    output_specs = {'robot': Robot}
    config_specs = {'moving_step': FloatParam(default_value=0.1, description="The moving step of the robot"), 'direction': StrParam(
        default_value="north", allowed_values=["north", "south", "east", "west"], description="The moving direction")}

    async def run(self, config: ConfigValues, inputs: TaskInputs) -> TaskOutputs:
        print(f"Moving {config.get_value('moving_step')}", flush=True)
        robot: Robot = inputs['robot']
        robot.move(direction=config.get_value('direction'), moving_step=config.get_value('moving_step'))
        return {'robot': robot}


@task_decorator("RobotEat", human_name="Eat task",
                short_description="This task emulates the meal of the robot before its flight!")
class RobotEat(Task):
    input_specs = {'robot': Robot, 'food': Optional[RobotFood]}
    output_specs = {'robot': Robot}
    config_specs = {
        'food_weight': FloatParam(default_value=3.14)
    }

    async def run(self, config: ConfigValues, inputs: TaskInputs) -> TaskOutputs:
        robot: Robot = inputs['robot']

        multiplicator: int = 1
        if inputs.has_resource('food'):
            food: RobotFood = inputs['food']
            multiplicator = food.multiplicator

        print(f"Eating {config.get_value('food_weight')} with multiplicator : {multiplicator}", flush=True)
        robot.weight += config.get_value('food_weight') * multiplicator
        return {'robot': robot}


@task_decorator("RobotWait", human_name="Wait task",
                short_description="This task emulates the resting time of the robot before its flight!")
class RobotWait(Task):
    input_specs = {'robot': Robot}
    output_specs = {'robot': Robot}
    config_specs = {
        # wait for .5 secs by default
        'waiting_time': FloatParam(default_value=0.5)
    }

    async def run(self, config: ConfigValues, inputs: TaskInputs) -> TaskOutputs:
        print(f"Waiting {config.get_value('waiting_time')}", flush=True)
        time.sleep(config.get_value('waiting_time'))
        return {'robot': inputs['robot']}


@task_decorator("RobotFly", human_name="Fly task",
                short_description="This task emulates the fly of the robot. It inherites the Move task.")
class RobotFly(RobotMove):
    config_specs = {'moving_step': FloatParam(default_value=1000.0, unit="km"), 'direction': StrParam(
        default_value="west", allowed_values=["north", "south", "east", "west"], description="The flying direction")}

    async def run(self, config: ConfigValues, inputs: TaskInputs) -> TaskOutputs:
        print("Start flying ...")
        return await super().run(config=config, inputs=inputs)


@task_decorator("RobotAdd")
class RobotAdd(Task):
    input_specs = {'robot': Robot, 'addon': RobotAddOn}
    output_specs = {'mega_robot': MegaRobot}
    config_specs = {}

    async def run(self, config: ConfigValues, inputs: TaskInputs) -> TaskOutputs:
        print("Add robot addon...")

        robot: Robot = inputs['robot']
        mega = MegaRobot.from_robot(robot)
        return {'mega_robot':  mega}


@task_decorator(unique_name="RobotAddOnCreate", human_name="The travel of `Astro`",
                short_description="This is the travel of astro composed of several steps")
class RobotAddOnCreate(Task):
    input_specs = {}
    output_specs = {'addon': RobotAddOn}
    config_specs = {}

    async def run(self, config: ConfigValues, inputs: TaskInputs) -> TaskOutputs:
        print("AddOn Create", flush=True)
        return {'addon': RobotAddOn()}


@task_decorator(unique_name="RobotSugarCreate", human_name="Create a sugar type of food",
                short_description="Create a sugar type of food")
class RobotSugarCreate(Task):
    """Task that create a sugar type of food and wait 3 secondes for it
    used in TestRobotwithSugarProtocol
    """
    input_specs = {}
    output_specs = {'sugar': RobotFood}
    config_specs = {}

    async def run(self, config: ConfigValues, inputs: TaskInputs) -> TaskOutputs:
        print("Create sugar", flush=True)
        food: RobotFood = RobotFood()
        food.multiplicator = 10
        return {'sugar': food}
