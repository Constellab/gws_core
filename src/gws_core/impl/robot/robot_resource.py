from typing import List

from gws_core.config.param_spec import StrParam

from ...resource.r_field import FloatRField, IntRField, ListRField
from ...resource.resource import Resource
from ...resource.resource_decorator import resource_decorator
from ...resource.view_decorator import view


@resource_decorator(unique_name="Robot")
class Robot(Resource):

    age: int = IntRField()
    position: List[float] = ListRField()
    weight: float = FloatRField()

    @classmethod
    def empty(cls) -> 'Robot':
        robot: Robot = Robot()
        # default values
        robot.age = 9
        robot.position = [0, 0]
        robot.weight = 70
        return robot

    def move(self, direction: str, moving_step: float):
        if direction == "north":
            self.position[1] += moving_step
        elif direction == "south":
            self.position[1] -= moving_step
        elif direction == "west":
            self.position[0] -= moving_step
        elif direction == "east":
            self.position[0] += moving_step

    @view(human_name="View position", specs={"test": StrParam(default_value="Nice")})
    def view_only_position(self, test: str = "Nice") -> List[float]:
        return self.position


@resource_decorator("RobotAddOn")
class RobotAddOn(Resource):
    pass


@resource_decorator("MegaRobot")
class MegaRobot(Robot):

    @classmethod
    def from_robot(cls, robot: Robot) -> 'MegaRobot':
        mega = MegaRobot()
        mega.position = robot.position
        mega.weight = robot.weight
        mega.age = robot.age
        return mega


@resource_decorator("RobotFood")
class RobotFood(Resource):

    multiplicator: int = IntRField()
