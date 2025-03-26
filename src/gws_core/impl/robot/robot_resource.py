import json
from typing import Dict, List

from pandas import DataFrame

from gws_core.config.config_specs import ConfigSpecs
from gws_core.model.typing_style import TypingStyle

from ...config.config_params import ConfigParams
from ...config.param.param_spec import StrParam
from ...resource.r_field.list_r_field import ListRField
from ...resource.r_field.primitive_r_field import FloatRField, IntRField
from ...resource.resource import Resource
from ...resource.resource_decorator import resource_decorator
from ...resource.view.view_decorator import view
from ..json.json_view import JSONView
from ..table.view.table_view import TableView
from ..text.text_view import TextView


@resource_decorator(unique_name="Robot", human_name="Robot", hide=True,
                    style=TypingStyle.material_icon("smart_toy", background_color="#2b6d57"))
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

    @view(view_type=JSONView, human_name="View position",
          specs=ConfigSpecs({"position": StrParam(default_value="latitude", allowed_values=['latitude', 'longitude'])}))
    def view_only_position(self, params: ConfigParams) -> JSONView:
        position: str = params.get_value('position')
        position_value = self.position[1] if position == 'latitude' else self.position[0]
        return JSONView({"position": position, "value": position_value})

    @view(view_type=TextView, human_name="View as text")
    def view_as_string(self, params: ConfigParams) -> TextView:
        str_ = json.dumps(self.to_dict())
        return TextView(str_)

    def to_dict(self) -> Dict:
        return {"age": self.age, "position": self.position, "weight": self.weight}


@resource_decorator("RobotAddOn", hide=True,
                    style=TypingStyle.material_icon("smart_toy", background_color="#2b6d57"))
class RobotAddOn(Resource):
    pass


@resource_decorator("MegaRobot", hide=True,
                    style=TypingStyle.material_icon("smart_toy", background_color="#2b6d57"))
class MegaRobot(Robot):

    @classmethod
    def from_robot(cls, robot: Robot) -> 'MegaRobot':
        mega = MegaRobot()
        mega.position = robot.position
        mega.weight = robot.weight
        mega.age = robot.age
        return mega


@resource_decorator("RobotFood", hide=True,
                    style=TypingStyle.material_icon("smart_toy", background_color="#2b6d57"))
class RobotFood(Resource):

    multiplicator: int = IntRField()

    @classmethod
    def empty(cls) -> 'RobotFood':
        food = RobotFood()
        food.multiplicator = 1
        return food
