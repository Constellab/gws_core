

from gws_core.config.config_params import ConfigParams
from gws_core.config.config_types import ConfigSpecs
from gws_core.config.param.param_spec import StrParam
from gws_core.document_template.document_template import DocumentTemplate
from gws_core.document_template.task.document_template_param import \
    DocumentTemplateParam
from gws_core.impl.rich_text.rich_text import RichText
from gws_core.impl.rich_text.rich_text_param import RichTextParam
from gws_core.io.io_spec import OutputSpec
from gws_core.io.io_specs import InputSpecs, OutputSpecs
from gws_core.task.task import Task
from gws_core.task.task_decorator import task_decorator
from gws_core.task.task_io import TaskInputs, TaskOutputs

from .note_resource import NoteResource


@task_decorator(
    unique_name="CreateNoteResource",
    human_name="Create note resource",
    short_description="Create an empty note resource or from a document template",
)
class CreateNoteResource(Task):
    """
    Create a note that can be exported to a note.
    """

    input_specs: InputSpecs = InputSpecs()

    output_specs: OutputSpecs = OutputSpecs({
        'note': OutputSpec(NoteResource, human_name='Note resource', short_description='New note resource')
    })

    config_specs: ConfigSpecs = {
        'template': DocumentTemplateParam(optional=True),
        'title': StrParam(human_name='Title', short_description='Title of the note resource', default_value='New note resource'),
        'note': RichTextParam(human_name='Note resource', short_description='Note resource content, this overrides the template',
                              optional=True)
    }

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        template: DocumentTemplate = params['template']
        title: str = params['title']
        note_param: RichText = params['note']

        note_resource = NoteResource()
        note_resource.title = title or 'New note resource'

        if note_param and not note_param.is_empty():
            note_resource.append_basic_rich_text(note_param)
        elif template is not None:
            note_resource = NoteResource.from_document_template(template,
                                                                title=title if title else None)

        return {
            'note': note_resource
        }