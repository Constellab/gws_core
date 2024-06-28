

from gws_core.config.config_params import ConfigParams
from gws_core.config.config_types import ConfigSpecs
from gws_core.config.param.param_spec import StrParam
from gws_core.io.io_spec import InputSpec, OutputSpec
from gws_core.io.io_specs import InputSpecs, OutputSpecs
from gws_core.report.task.report_resource import ReportResource
from gws_core.task.task import Task
from gws_core.task.task_decorator import task_decorator
from gws_core.task.task_io import TaskInputs, TaskOutputs

from .enote_resource import ENoteResource


@task_decorator("GenerateReportFromENote", human_name="Generate report from e-note",
                short_description="Task to generate a report from an e-note")
class GenerateReportFromENote(Task):
    """
    Generate a report from the note content.
    """

    input_specs: InputSpecs = InputSpecs({
        'enote': InputSpec(ENoteResource, human_name='E-note')
    })

    output_specs: OutputSpecs = OutputSpecs({
        'report': OutputSpec(ReportResource, human_name='Report', short_description='New report')
    })

    config_specs: ConfigSpecs = {
        'title': StrParam(human_name='Report title', short_description='This overides the e-note title',
                          optional=True)
    }

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        enote_resource: ENoteResource = inputs['enote']

        report = enote_resource.export_as_report(params['title'])

        return {
            'report': ReportResource(report.id)
        }
