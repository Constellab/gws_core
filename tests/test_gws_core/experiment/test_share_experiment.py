

from gws_core.experiment.experiement_loader import ExperimentLoader
from gws_core.experiment.experiment_enums import ExperimentStatus
from gws_core.experiment.experiment_interface import IExperiment
from gws_core.experiment.experiment_zipper import ExperimentZipper
from gws_core.impl.file.file_helper import FileHelper
from gws_core.impl.robot.robot_tasks import RobotCreate, RobotMove
from gws_core.task.plug import Sink
from gws_core.test.base_test_case import BaseTestCase
from gws_core.test.gtest import GTest


# test_share_experiment
class TestShareExperiment(BaseTestCase):

    def test_share_experiment(self):

        # Create and run an experiment
        project = GTest.create_default_project()
        experiment = IExperiment(title='Test experiment', project=project)
        protocol = experiment.get_protocol()
        create = protocol.add_process(RobotCreate, 'create')
        move = protocol.add_process(RobotMove, 'move', config_params={'moving_step': 100})
        protocol.add_connector(create >> 'robot', move << 'robot')
        protocol.add_sink('sink', move >> 'robot')
        experiment.run()

        # Zip the experiment
        zipped_experiment = ExperimentZipper(GTest.get_test_user())

        zipped_experiment.add_experiment(experiment.get_experiment_model().id)
        result = zipped_experiment.close_zip()

        # Check the zip file
        self.assertTrue(FileHelper.exists_on_os(result))

        # Unzip the experiment
        experiment_loader = ExperimentLoader.from_compress_file(result)
        experiment = experiment_loader.load_experiment()

        experiment.save()
        experiment_loader.protocol_model.save_full()

        self.assertEqual(experiment.title, 'Test experiment')
        self.assertEqual(experiment.project.id, project.id)
        self.assertEqual(experiment.status, ExperimentStatus.SUCCESS)

        protocol_model = experiment.protocol_model
        self.assertEqual(len(protocol_model.processes), 3)
        self.assertEqual(len(protocol_model.connectors), 2)
        self.assertEqual(protocol_model.get_process('create').process_typing_name, RobotCreate._typing_name)
        self.assertEqual(protocol_model.get_process('move').process_typing_name, RobotMove._typing_name)
        self.assertEqual(protocol_model.get_process('move').config.get_value('moving_step'), 100)
        self.assertEqual(protocol_model.get_process('sink').process_typing_name, Sink._typing_name)
