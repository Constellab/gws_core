from typing import List

from ...resource.resource import Resource, SerializedResourceData
from ...resource.resource_decorator import ResourceDecorator


@ResourceDecorator("Robot")
class Robot(Resource):

    age: int
    position: List[float]
    weight: int

    @classmethod
    def empty(cls) -> 'Robot':
        robot: Robot = Robot()
        # default values
        robot.age = 9
        robot.position = [0, 0]
        robot.weight = 70
        return robot

    def serialize_data(self) -> SerializedResourceData:
        return {
            "age": self.age,
            "position": self.position,
            "weight": self.weight,
        }

    def deserialize_data(self, data: SerializedResourceData) -> None:
        if data:
            self.age = data["age"]
            self.position = data["position"]
            self.weight = data["weight"]

    def move(self, direction: str, moving_step: float):
        if direction == "north":
            self.position[1] += moving_step
        elif direction == "south":
            self.position[1] -= moving_step
        elif direction == "west":
            self.position[0] -= moving_step
        elif direction == "east":
            self.position[0] += moving_step


@ResourceDecorator("RobotAddOn")
class RobotAddOn(Resource):
    def serialize_data(self) -> SerializedResourceData:
        return {}

    def deserialize_data(self, data: SerializedResourceData) -> None:
        pass


@ResourceDecorator("MegaRobot")
class MegaRobot(Robot):

    @classmethod
    def from_robot(cls, robot: Robot) -> 'MegaRobot':
        mega = MegaRobot()
        mega.position = robot.position
        mega.weight = robot.weight
        mega.age = robot.weight
        return mega


@ResourceDecorator("RobotFood")
class RobotFood(Resource):

    multiplicator: int

    def serialize_data(self) -> SerializedResourceData:
        return {
            "multiplicator": self.multiplicator,
        }

    def deserialize_data(self, data: SerializedResourceData) -> None:
        if data:
            self.multiplicator = data['multiplicator']
