import json
from typing import Dict, List

from pandas import DataFrame

from ...config.param_spec import StrParam
from ...resource.r_field import FloatRField, IntRField, ListRField
from ...resource.resource import Resource
from ...resource.resource_decorator import resource_decorator
from ...resource.view_decorator import view
from ..json.json_view import JsonView
from ..table.view.table_view import TableView
from ..text.view.text_view import TextView


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

    @view(view_type=JsonView, human_name="View position",
          specs={"position": StrParam(default_value="latitude", allowed_values=['latitude', 'longitude'])})
    def view_only_position(self, position: str) -> JsonView:
        position_value = self.position[1] if position == 'latitude' else self.position[0]
        return JsonView({"position": position, "value": position_value})

    @view(view_type=TableView, human_name="View as csv")
    def view_as_csv(self) -> TableView:
        dataframe: DataFrame = DataFrame.from_dict(self.to_dict())
        return TableView(dataframe)

    @view(view_type=TextView, human_name="View as text")
    def view_as_string(self) -> TextView:
        str_ = json.dumps(self.to_dict())
        return TextView(str_)

    def to_dict(self) -> Dict:
        return {"age": self.age, "position": self.position, "weight": self.weight}


@ resource_decorator("RobotAddOn")
class RobotAddOn(Resource):
    pass


@ resource_decorator("MegaRobot")
class MegaRobot(Robot):

    @ classmethod
    def from_robot(cls, robot: Robot) -> 'MegaRobot':
        mega = MegaRobot()
        mega.position = robot.position
        mega.weight = robot.weight
        mega.age = robot.age
        return mega


@ resource_decorator("RobotFood")
class RobotFood(Resource):

    multiplicator: int = IntRField()
