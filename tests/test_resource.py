# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from gws_core import (BaseTestCase, Experiment, ExperimentService, GTest,
                      ProcessableFactory, ResourceModel, Robot, RobotCreate,
                      TaskModel)


class TestResource(BaseTestCase):

    async def test_resource(self):
        GTest.print("Resource")

        task_model: TaskModel = ProcessableFactory.create_task_model_from_type(
            task_type=RobotCreate, instance_name="create")
        experiment = ExperimentService.create_experiment_from_task_model(task_model)

        experiment: Experiment = await ExperimentService.run_experiment(experiment)

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
