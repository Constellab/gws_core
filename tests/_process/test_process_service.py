# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from gws_core import (BaseTestCase, IExperiment, IProcess, IProtocol,
                      RobotCreate, Wait)
from gws_core.core.utils.logger import Logger
from gws_core.core.utils.settings import Settings
from gws_core.impl.file.file_helper import FileHelper
from gws_core.process.process_service import ProcessService


# test_process_service
class TestProcessService(BaseTestCase):

    def test_get_log(self):

        # create a simple waiting experiment to let the log be created
        experiment = IExperiment()
        protocol: IProtocol = experiment.get_protocol()

        create_robot: IProcess = protocol.add_task(RobotCreate, 'create_robot')
        wait: IProcess = protocol.add_task(Wait, 'wait', {'waiting_time': 1})
        protocol.add_connector(create_robot >> 'robot', wait << 'resource')

        experiment.run()

        logs = ProcessService.get_logs_of_process('TASK', wait.refresh()._process_model.id, is_sub_process=False)
        self.assertTrue(len(logs.logs) > 0)
        # search log with content : Waiting 1 seconds
        self.assertTrue(len([log for log in logs.logs if 'Waiting 1 sec' in log.content]) > 0)

    def setUp(self) -> None:
        # force init the logger
        FileHelper.delete_dir_content(Settings.get_instance().get_log_dir())
        Logger._logger = None
        Logger(level='INFO', _is_experiment_process=False)

    def tearDown(self) -> None:
        FileHelper.delete_dir_content(Settings.get_instance().get_log_dir())
