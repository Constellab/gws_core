

import os

from gws_core.config.config_params import ConfigParams
from gws_core.config.config_types import ConfigSpecs
from gws_core.config.param.param_spec import StrParam
from gws_core.core.utils.compress.zip_compress import ZipCompress
from gws_core.core.utils.settings import Settings
from gws_core.credentials.credentials_param import CredentialsParam
from gws_core.credentials.credentials_type import CredentialsType
from gws_core.external_source.biolector_xt.biolector_xt_dto import \
    CredentialsDataBiolector
from gws_core.external_source.biolector_xt.biolector_xt_service import \
    BiolectorXTService
from gws_core.impl.file.file import File
from gws_core.impl.file.file_helper import FileHelper
from gws_core.impl.table.table import Table
from gws_core.impl.table.tasks.table_importer import TableImporter
from gws_core.io.io_spec import InputSpec, OutputSpec
from gws_core.io.io_specs import InputSpecs, OutputSpecs
from gws_core.model.typing_style import TypingStyle
from gws_core.task.task import Task
from gws_core.task.task_decorator import task_decorator
from gws_core.task.task_io import TaskInputs, TaskOutputs


@task_decorator(unique_name="BiolectorDownloadExperiment",
                short_description="Download the reuslt of an experiment from Biolector XT",
                style=TypingStyle.community_icon("bioreactor"), hide=True)
class BiolectorDownloadExperiment(Task):

    config_specs: ConfigSpecs = {
        'experiment_id': StrParam(human_name="Experiment ID",
                                  short_description="The ID of the BiolectorXT experiment to download"),
        'credentials': CredentialsParam(credentials_type=CredentialsType.OTHER),
    }
    input_specs: InputSpecs = InputSpecs({
        # TODO TO REMOVE, this is to test the unzip
        'file': InputSpec(File, human_name="The file to import")
    })
    output_specs: OutputSpecs = OutputSpecs({'result': OutputSpec(Table)})

    zip_path = None

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:

        # Get the experiment ID
        experiment_id = params.get_value('experiment_id')

        biolector_credentials: CredentialsDataBiolector
        try:
            biolector_credentials = CredentialsDataBiolector.from_json(params.get_value('credentials'))
        except Exception as e:
            raise ValueError("Invalid credentials data: " + str(e))

        # # download experiment
        # self.log_info_message(f"Downloading experiment {experiment_id} from Biolector XT")
        # service = BiolectorXTService(biolector_credentials)
        # zip_path = service.download_experiment(experiment_id)

        self.zip_path = inputs['file'].path
        # unzip the file
        self.log_info_message("Unzipping the downloaded file")
        tmp_dir = self.create_tmp_dir()
        ZipCompress.decompress(self.zip_path, tmp_dir)

        # read the csv result file
        # find the csv file in the unzipped folder, no recursion
        csv_file = None
        for file in os.listdir(tmp_dir):
            if file.endswith('.csv'):
                csv_file = os.path.join(tmp_dir, file)
                break

        if csv_file is None:
            raise ValueError("No CSV file found in the downloaded experiment")

        self.log_info_message(f"Importing csv file: {csv_file}")

        table = TableImporter.call(File(csv_file), {
            'file_format': 'csv',
            'delimiter': ';',
            'header': 0,
            'format_header_names': True,
            'index_column': -1,
        })

        return {'result': table}

    def run_after_task(self) -> None:
        super().run_after_task()
        if self.zip_path:
            FileHelper.delete_file(self.zip_path)
