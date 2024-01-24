# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from gws_core.config.config_params import ConfigParams
from gws_core.config.config_types import ConfigSpecs
from gws_core.io.io_spec import InputSpec, OutputSpec
from gws_core.io.io_specs import InputSpecs, OutputSpecs
from gws_core.report.task.note_resource import NoteResource
from gws_core.report.task.report_resource import ReportResource
from gws_core.task.task import Task
from gws_core.task.task_decorator import task_decorator
from gws_core.task.task_io import TaskInputs, TaskOutputs


@task_decorator("GenerateReportFromNote", human_name="Generate report from note",
                short_description="Task to generate a report from a note")
class CreateNote(Task):
    """
    Create a note that can be exported to a report.
    """

    input_specs: InputSpecs = InputSpecs({
        'note': InputSpec(NoteResource, human_name='Note')
    })

    output_specs: OutputSpecs = OutputSpecs({
        'report': OutputSpec(ReportResource, human_name='Note', short_description='New note')
    })

    config_specs: ConfigSpecs = {
    }

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        note_resource: NoteResource = inputs['note']

        report = note_resource.export_as_report()

        return {
            'report': ReportResource(report.id)
        }
