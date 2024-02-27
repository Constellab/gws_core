# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from gws_core.config.config_params import ConfigParams
from gws_core.config.config_types import ConfigSpecs
from gws_core.config.param.param_spec import StrParam
from gws_core.io.io_spec import OutputSpec
from gws_core.io.io_specs import InputSpecs, OutputSpecs
from gws_core.report.report_dto import ReportSaveDTO
from gws_core.report.report_service import ReportService
from gws_core.report.template.report_template import ReportTemplate
from gws_core.report.template.report_template_param import ReportTemplateParam
from gws_core.task.task import Task
from gws_core.task.task_decorator import task_decorator
from gws_core.task.task_io import TaskInputs, TaskOutputs

from .report_resource import ReportResource


@task_decorator(
    unique_name="CreateReport",
    short_description="Create a report",
    hide=True,
)
class CreateReport(Task):
    """
    Task to create a report. The report is directly create and accessible in the reports sections.
    The report is updatable and a ReportResource is returned by this task to access and modify the report.

    It is recommended to place this task at the end of a workflow to create a report with the results of the workflow.
    To assure the report is not created if the workflow fails.
    """

    input_specs: InputSpecs = InputSpecs()

    output_specs: OutputSpecs = OutputSpecs({
        'report': OutputSpec(ReportResource, human_name='Report', short_description='Report created')
    })

    config_specs: ConfigSpecs = {
        'template': ReportTemplateParam(optional=True),
        'title': StrParam(human_name='Title', short_description='Title of the report', optional=True),
    }

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        template: ReportTemplate = params['template']
        title: str = params['title']

        if not title:
            if template:
                title = template.title
            else:
                title = 'New generated report'
        report_dto = ReportSaveDTO(title=title, template_id=template.id if template else None)

        report = ReportService.create(report_dto)

        self.log_info_message(f"Report '{report.title}' created")

        return {
            'report': ReportResource(report.id)
        }
