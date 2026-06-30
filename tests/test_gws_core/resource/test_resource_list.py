from gws_core import InputSpec
from gws_core.impl.robot.robot_resource import Robot
from gws_core.io.dynamic_io import DynamicInputs
from gws_core.resource.resource_dto import ResourceOrigin
from gws_core.resource.resource_model import ResourceModel
from gws_core.resource.resource_set.resource_list import ResourceList
from gws_core.resource.resource_set.resource_list_tasks import (
    ResourceListPicker,
    ResourceListStacker,
)
from gws_core.task.task_runner import TaskRunner
from gws_core.test.base_test_case import BaseTestCase


# test_resource_list
class TestResourceList(BaseTestCase):
    def test_resource_list_stacker(self):
        robot_1 = Robot.empty()
        ResourceModel.save_from_resource(robot_1, ResourceOrigin.UPLOADED)
        robot_2 = Robot.empty()
        robot_2.name = "robot_2"
        ResourceModel.save_from_resource(robot_2, ResourceOrigin.UPLOADED)

        robot_3 = Robot.empty()
        robot_3.name = "robot_3"
        ResourceModel.save_from_resource(robot_3, ResourceOrigin.UPLOADED)
        resource_list: ResourceList = ResourceList()
        resource_list.add_resource(robot_3, create_new_resource=False)
        ResourceModel.save_from_resource(resource_list, ResourceOrigin.UPLOADED)

        task_runner = TaskRunner(
            ResourceListStacker,
            inputs={
                "resource_1": robot_1,
                "resource_2": robot_2,
                "resource_3": None,
                "resource_4": resource_list,
            },
            input_specs=DynamicInputs(
                {
                    "resource_1": InputSpec(Robot),
                    "resource_2": InputSpec(Robot),
                    "resource_3": InputSpec(Robot, optional=True),
                    "resource_4": InputSpec(ResourceList),
                }
            ),
        )

        outputs = task_runner.run()

        output_resource_list = outputs.get("resource_list")

        self.assertIsInstance(output_resource_list, ResourceList)
        assert isinstance(output_resource_list, ResourceList)
        # robot_1, robot_2 and the flattened robot_3
        self.assertEqual(len(output_resource_list), 3)
        uids = {resource.uid for resource in output_resource_list}
        self.assertEqual(uids, {robot_1.uid, robot_2.uid, robot_3.uid})

    def test_resource_list_picker(self):
        robot_1 = Robot.empty()
        robot_2 = Robot.empty()
        robot_2.name = "robot_2"

        resource_list: ResourceList = ResourceList()
        resource_list.add_resource(robot_1)
        resource_list.add_resource(robot_2)
        ResourceModel.save_from_resource(resource_list, ResourceOrigin.UPLOADED)

        task_runner = TaskRunner(
            ResourceListPicker,
            params={"indexes": [{"index": 1}]},
            inputs={"resource_list": resource_list},
        )

        outputs = task_runner.run()

        # DynamicOutputs distributes the picked resources over individual output ports
        picked = list(outputs.values())
        self.assertEqual(len(picked), 1)
        picked_robot = picked[0]
        self.assertIsInstance(picked_robot, Robot)
        assert picked_robot is not None
        self.assertEqual(picked_robot.uid, robot_2.uid)
