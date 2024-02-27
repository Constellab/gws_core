# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com
from gws_core.config.config_params import ConfigParams
from gws_core.config.config_types import ConfigSpecs
from gws_core.io.io_spec import OutputSpec
from gws_core.io.io_specs import InputSpecs, OutputSpecs
from gws_core.report.report_param import ReportParam
from gws_core.task.task import Task
from gws_core.task.task_decorator import task_decorator
from gws_core.task.task_io import TaskInputs, TaskOutputs

from .report_resource import ReportResource


@task_decorator(
    unique_name="SelectReport",
    short_description="Select a report",
    hide=True,
)
class SelectReport(Task):
    """
    Task to select an existing report and return a ReportResource to access and modify the report.
    """

    input_specs: InputSpecs = InputSpecs()

    output_specs: OutputSpecs = OutputSpecs({
        'report': OutputSpec(ReportResource, human_name='Report', short_description='Report selected')
    })

    config_specs: ConfigSpecs = {
        'report': ReportParam(),
    }

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        return {
            'report': params['report']
        }
