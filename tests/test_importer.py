

from gws_core import (BaseTestCase, File, IExperiment, ITask, Table,
                      TableImporter)


class TestImporter(BaseTestCase):

    async def test_importer(self):
        file: File = File(path=self.get_test_data_path('iris.csv'))

        experiment: IExperiment = IExperiment()
        task: ITask = experiment.get_protocol().add_task(TableImporter, 'table_importer')
        task.set_input('file', file)

        await experiment.run()

        self.assertIsInstance(task.get_output('resource'), Table)
