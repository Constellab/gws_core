

from gws_core.experiment.experiment_interface import IExperiment
from gws_core.impl.file.file import File
from gws_core.impl.file.file_service import FileService
from gws_core.impl.table.table_tasks import TableImporter
from gws_core.task.task_interface import ITask
from gws_core.test.base_test_case import BaseTestCase


class TestImporter(BaseTestCase):

    async def test_importer(self):

        file: File = File(path=self.get_test_data_path('iris.csv'))
        # file_resource = FileService.create_file_model(file)

        experiment: IExperiment = IExperiment()
        task: ITask = experiment.get_protocol().add_task(TableImporter, 'table_importer')
        task.set_input('file', file)

        await experiment.run()
