# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com
from typing import List

from gws_core import (BaseTestCase, Experiment, ExperimentService, GTest,
                      ProcessFactory, ResourceModel, Robot, RobotCreate,
                      TaskModel)
from gws_core.experiment.experiment_run_service import ExperimentRunService
from gws_core.resource.r_field import IntRField, ListRField
from gws_core.resource.resource import Resource
from gws_core.resource.resource_decorator import resource_decorator
from gws_core.resource.resource_model import ResourceOrigin


@resource_decorator(unique_name="TestResourceFields")
class TestResourceFields(Resource):

    age: int = IntRField()
    position: List[float] = ListRField()

    weight: int = IntRField()


class TestResource(BaseTestCase):

    async def test_resource(self):
        GTest.print("Resource")

        task_model: TaskModel = ProcessFactory.create_task_model_from_type(
            task_type=RobotCreate, instance_name="create")
        experiment = ExperimentService.create_experiment_from_task_model(task_model)

        experiment: Experiment = await ExperimentRunService.run_experiment(experiment)

        create: TaskModel = experiment.protocol_model.get_process('create')

        # Check that the resource model was generated
        resource_model: ResourceModel = create.out_port('robot').resource_model
        self.assertIsNotNone(resource_model.id)
        self.assertTrue(isinstance(resource_model, ResourceModel))

        # Check that the resource is a Robot
        robot: Robot = resource_model.get_resource()
        self.assertTrue(isinstance(robot, Robot))

        # Check the to_json
        resource_model.to_json(deep=True)

    def test_2(self):
        resource = TestResourceFields()
        resource.position = [5, 2]
        resource.age = 12
        resource.weight = None

        resource_model: ResourceModel = ResourceModel.from_resource(resource, origin=ResourceOrigin.IMPORTED)

        self.assertEqual(len(resource_model.data), 3)
        self.assertIsNotNone(resource_model.kv_store_path)

        # generate the resource from the resource model and check its values
        new_resource: TestResourceFields = resource_model.get_resource(new_instance=True)

        self.assertEqual(new_resource.age, 12)
        self.assertIsNone(new_resource.weight)
        self.assertEqual(new_resource.position[0], 5)
        self.assertEqual(new_resource.position[1], 2)
