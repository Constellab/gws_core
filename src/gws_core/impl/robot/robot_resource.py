from typing import List

from ...resource.resource import Resource
from ...resource.resource_data import ResourceData
from ...resource.resource_decorator import ResourceDecorator


@ResourceDecorator("Robot")
class Robot(Resource):
    def __init__(self, data: ResourceData = None):
        super().__init__(data)

        if self.data.is_empty():
            self.data.set_values({
                "age": 9,
                "position": [0, 0],
                "weight": 70
            })

    @property
    def age(self) -> int:
        return self.data['age']

    @property
    def position(self) -> List[int]:
        return self.data['position']

    @property
    def weight(self) -> int:
        return self.data['weight']

    def set_position(self, val: List[int]):
        self.data['position'] = val

    def set_weight(self, val: int):
        self.data['weight'] = val

    def set_age(self, val: int):
        self.data['age'] = val


@ResourceDecorator("RobotAddOn")
class RobotAddOn(Resource):
    pass


@ResourceDecorator("MegaRobot")
class MegaRobot(Robot):
    pass


@ResourceDecorator("RobotFood")
class RobotFood(Resource):
    @property
    def multiplicator(self) -> int:
        return self.data['multiplicator']

    def set_multiplicator(self, val: int):
        self.data['multiplicator'] = val
