# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from gws_core.config.config_params import ConfigParams
from gws_core.config.config_types import ConfigSpecs
from gws_core.config.param.param_spec import StrParam
from gws_core.impl.rich_text.rich_text import RichText
from gws_core.impl.rich_text.rich_text_param import RichTextParam
from gws_core.io.io_spec import OutputSpec
from gws_core.io.io_specs import InputSpecs, OutputSpecs
from gws_core.report.task.note_resource import NoteResource
from gws_core.report.template.report_template import ReportTemplate
from gws_core.report.template.report_template_param import ReportTemplateParam
from gws_core.task.task import Task
from gws_core.task.task_decorator import task_decorator
from gws_core.task.task_io import TaskInputs, TaskOutputs


@task_decorator(
    unique_name="CreateNote",
    short_description="Create a note",
)
class CreateNote(Task):
    """
    Create a note that can be exported to a report.
    """

    input_specs: InputSpecs = InputSpecs()

    output_specs: OutputSpecs = OutputSpecs({
        'note': OutputSpec(NoteResource, human_name='Note', short_description='New note')
    })

    config_specs: ConfigSpecs = {
        'template': ReportTemplateParam(optional=True),
        'title': StrParam(human_name='Title', short_description='Title of the note', default_value='New note'),
        'note': RichTextParam(human_name='Note', short_description='Note content, this overrides the template',
                              optional=True)
    }

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        template: ReportTemplate = params['template']
        title: str = params['title']
        note_param: RichText = params['note']

        note_resource = NoteResource(title=title or 'New note')

        if note_param is not None:
            note_resource.rich_text = note_param
        elif template is not None:
            note_resource.rich_text = RichText(template.content)

        return {
            'note': note_resource
        }
