

from gws_core import BaseTestCase, IExperiment, IProcess, IProtocol
from gws_core.core.utils.logger import Logger
from gws_core.core.utils.settings import Settings
from gws_core.impl.file.file_helper import FileHelper
from gws_core.impl.robot.robot_tasks import RobotCreate
from gws_core.process.process_service import ProcessService
from gws_core.task.plug import Wait


# test_process_service
class TestProcessService(BaseTestCase):

    def test_get_log(self):

        # create a simple waiting experiment to let the log be created
        experiment = IExperiment()

        # force init the logger
        FileHelper.delete_dir_content(Settings.get_instance().get_log_dir())
        Logger.clear_logger()
        # initialize the logger associated to the experiment
        Logger(Settings.build_log_dir(True), level='INFO', experiment_id=experiment.get_model().id)

        protocol: IProtocol = experiment.get_protocol()

        create_robot: IProcess = protocol.add_task(RobotCreate, 'create_robot')
        wait: IProcess = protocol.add_task(Wait, 'wait', {'waiting_time': 1})
        protocol.add_connector(create_robot >> 'robot', wait << 'resource')

        experiment.run()

        logs = ProcessService.get_logs_of_process('TASK', wait.refresh()._process_model.id)
        self.assertTrue(len(logs.logs) > 0)
        # search log with content : Waiting 1 seconds
        self.assertTrue(len([log for log in logs.logs if 'Waiting 1 sec' in log.message]) > 0)

    def tearDown(self) -> None:
        FileHelper.delete_dir_content(Settings.get_instance().get_log_dir())
