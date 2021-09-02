from typing import List

from ...resource.resource import Resource
from ...resource.resource_decorator import ResourceDecorator
from ...resource.resource_serialized import ResourceSerialized


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

    def serialize(self) -> ResourceSerialized:
        return ResourceSerialized(light_data={
            "age": self.age,
            "position": self.position,
            "weight": self.weight,
        })

    def deserialize(self, resource_serialized: ResourceSerialized) -> None:
        if resource_serialized.has_light_data():
            self.age = resource_serialized.light_data["age"]
            self.position = resource_serialized.light_data["position"]
            self.weight = resource_serialized.light_data["weight"]

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
    def serialize(self) -> ResourceSerialized:
        return ResourceSerialized(light_data={})

    def deserialize(self, resource_serialized: ResourceSerialized) -> None:
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

    def serialize(self) -> ResourceSerialized:
        return ResourceSerialized(light_data={
            "multiplicator": self.multiplicator,
        })

    def deserialize(self, resource_serialized: ResourceSerialized) -> None:
        if resource_serialized.has_light_data():
            self.multiplicator = resource_serialized.light_data['multiplicator']
