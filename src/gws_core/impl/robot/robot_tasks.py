# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


import time

from gws_core.config.param.param_spec import FloatParam, StrParam
from gws_core.io.io_spec import InputSpec, OutputSpec
from gws_core.io.io_specs import InputSpecs, OutputSpecs

from ...config.config_params import ConfigParams
from ...impl.robot.robot_resource import (MegaRobot, Robot, RobotAddOn,
                                          RobotFood)
from ...task.task import Task
from ...task.task_decorator import task_decorator
from ...task.task_io import TaskInputs, TaskOutputs


@task_decorator("RobotCreate", human_name="Create robot", short_description="This task creates a robot", hide=True)
class RobotCreate(Task):
    input_specs = InputSpecs({})  # no required input
    output_specs = OutputSpecs({'robot': OutputSpec(Robot)})
    config_specs = {}

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        robot: Robot = Robot.empty()

        return {'robot': robot}


@task_decorator("RobotMove", human_name="Move robot",
                short_description="This task emulates a short moving step of the robot", hide=True)
class RobotMove(Task):
    input_specs = InputSpecs({'robot': InputSpec(Robot, human_name="Robot",
                                                 short_description="The robot to feed")})  # just for testing
    output_specs = OutputSpecs({'robot': OutputSpec(
        Robot), 'food': OutputSpec(RobotFood, is_optional=True)})
    config_specs = {'moving_step': FloatParam(default_value=0.1, short_description="The moving step of the robot"), 'direction': StrParam(
        default_value="north", allowed_values=["north", "south", "east", "west"], short_description="The moving direction")}

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        robot: Robot = inputs['robot']
        robot.move(direction=params.get_value('direction'),
                   moving_step=params.get_value('moving_step'))
        return {'robot': robot, 'food': None}


@task_decorator("RobotEat", human_name="Eat task",
                short_description="This task emulates the meal of the robot before its flight!", hide=True)
class RobotEat(Task):
    input_specs = InputSpecs({'robot': InputSpec(
        Robot), 'food': InputSpec(RobotFood, is_optional=True)})
    output_specs = OutputSpecs({'robot': OutputSpec(Robot)})
    config_specs = {
        'food_weight': FloatParam(default_value=3.14)
    }

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        robot: Robot = inputs['robot']

        multiplicator: int = 1
        if inputs.has_resource('food'):
            food: RobotFood = inputs['food']
            multiplicator = food.multiplicator

        robot.weight += params.get_value('food_weight') * multiplicator
        return {'robot': robot}


@task_decorator("RobotWait", human_name="Wait task",
                short_description="This task emulates the resting time of the robot before its flight!", hide=True)
class RobotWait(Task):
    input_specs = InputSpecs({'robot': InputSpec(Robot)})
    output_specs = OutputSpecs({'robot': OutputSpec(Robot)})
    config_specs = {
        # wait for .5 secs by default
        'waiting_time': FloatParam(default_value=0.5)
    }

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        time.sleep(params.get_value('waiting_time'))
        return {'robot': inputs['robot']}


@task_decorator("RobotFly", human_name="Fly task",
                short_description="This task emulates the fly of the robot. It inherites the Move task.", hide=True)
class RobotFly(RobotMove):
    config_specs = {'moving_step': FloatParam(default_value=1000.0, unit="km"), 'direction': StrParam(
        default_value="west", allowed_values=["north", "south", "east", "west"], short_description="The flying direction")}

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        return super().run(params, inputs)


@task_decorator("RobotAdd", hide=True)
class RobotAdd(Task):
    input_specs = InputSpecs({'robot': InputSpec(Robot), 'addon': InputSpec(RobotAddOn)})
    output_specs = OutputSpecs({'mega_robot': OutputSpec(MegaRobot)})
    config_specs = {}

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:

        robot: Robot = inputs['robot']
        mega = MegaRobot.from_robot(robot)
        return {'mega_robot':  mega}


@task_decorator(unique_name="RobotAddOnCreate", human_name="The travel of `Astro`",
                short_description="This is the travel of astro composed of several steps", hide=True)
class RobotAddOnCreate(Task):
    output_specs = OutputSpecs({'addon': OutputSpec(RobotAddOn)})
    config_specs = {}

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        return {'addon': RobotAddOn()}


@task_decorator(unique_name="RobotSugarCreate", human_name="Create a sugar type of food",
                short_description="Create a sugar type of food", hide=True)
class RobotSugarCreate(Task):
    """Task that create a sugar type of food and wait 3 secondes for it
    used in TestRobotWithSugarProtocol
    """
    output_specs = OutputSpecs({'sugar': OutputSpec(RobotFood)})
    config_specs = {}

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        food: RobotFood = RobotFood()
        food.multiplicator = 10
        return {'sugar': food}
