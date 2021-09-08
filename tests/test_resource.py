# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from gws_core import BaseTestCase, GTest
from gws_core.experiment.experiment import Experiment
from gws_core.experiment.experiment_service import ExperimentService
from gws_core.impl.robot.robot_process import RobotCreate
from gws_core.impl.robot.robot_resource import Robot
from gws_core.process.process_model import ProcessModel
from gws_core.processable.processable_factory import ProcessableFactory
from gws_core.resource.resource_model import ResourceModel


class TestResource(BaseTestCase):

    async def test_resource(self):
        GTest.print("Resource")

        process: ProcessModel = ProcessableFactory.create_process_model_from_type(
            process_type=RobotCreate, instance_name="create")
        experiment = ExperimentService.create_experiment_from_process_model(process)

        experiment: Experiment = await ExperimentService.run_experiment(experiment)

        create: ProcessModel = experiment.protocol.get_process('create')

        # Check that the resource model was generated
        resource_model: ResourceModel = create.out_port('robot').resource_model
        self.assertIsNotNone(resource_model.id)
        self.assertTrue(isinstance(resource_model, ResourceModel))

        # Check that the resource is a Robot
        robot: Robot = resource_model.get_resource()
        self.assertTrue(isinstance(robot, Robot))

        # Check the to_json
        resource_model.to_json(deep=True)
