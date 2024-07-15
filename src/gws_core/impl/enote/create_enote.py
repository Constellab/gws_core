

from gws_core.config.config_params import ConfigParams
from gws_core.config.config_types import ConfigSpecs
from gws_core.config.param.param_spec import StrParam
from gws_core.impl.rich_text.rich_text import RichText
from gws_core.impl.rich_text.rich_text_param import RichTextParam
from gws_core.io.io_spec import OutputSpec
from gws_core.io.io_specs import InputSpecs, OutputSpecs
from gws_core.report.template.report_template import ReportTemplate
from gws_core.report.template.report_template_param import ReportTemplateParam
from gws_core.task.task import Task
from gws_core.task.task_decorator import task_decorator
from gws_core.task.task_io import TaskInputs, TaskOutputs

from .enote_resource import ENoteResource


@task_decorator(
    unique_name="CreateENote",
    human_name="Create e-note",
    short_description="Create an empty e-note or from a report template",
)
class CreateENote(Task):
    """
    Create a note that can be exported to a report.
    """

    input_specs: InputSpecs = InputSpecs()

    output_specs: OutputSpecs = OutputSpecs({
        'enote': OutputSpec(ENoteResource, human_name='E-note', short_description='New e-note')
    })

    config_specs: ConfigSpecs = {
        'template': ReportTemplateParam(optional=True),
        'title': StrParam(human_name='Title', short_description='Title of the e-note', default_value='New e-note'),
        'enote': RichTextParam(human_name='E-note', short_description='E-note content, this overrides the template',
                               optional=True)
    }

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        template: ReportTemplate = params['template']
        title: str = params['title']
        enote_param: RichText = params['enote']

        enote_resource = ENoteResource()

        enote_resource.title = title or 'New e-note'
        if enote_param and not enote_param.is_empty():
            enote_resource.append_report_rich_text(enote_param)
        elif template is not None:
            rich_text = RichText(template.content)
            enote_resource.append_report_rich_text(rich_text)
            enote_resource.title = title or template.title

        return {
            'enote': enote_resource
        }
