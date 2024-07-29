
from gws_core.config.config_params import ConfigParams
from gws_core.config.config_types import ConfigSpecs
from gws_core.document_template.document_template import DocumentTemplate
from gws_core.document_template.task.document_template_param import \
    DocumentTemplateParam
from gws_core.document_template.task.document_template_resource import \
    DocumentTemplateResource
from gws_core.io.io_spec import OutputSpec
from gws_core.io.io_specs import InputSpecs, OutputSpecs
from gws_core.task.task import Task
from gws_core.task.task_decorator import task_decorator
from gws_core.task.task_io import TaskInputs, TaskOutputs


@task_decorator(
    unique_name="SelectDocumentTemplate",
    short_description="Select a document template",
)
class SelectDocumentTemplate(Task):
    """
    Task to select an existing document template and return a DocumentTemplateResource to access the DocumentTemplate.
    """

    input_specs: InputSpecs = InputSpecs()

    output_specs: OutputSpecs = OutputSpecs({
        'document_template': OutputSpec(DocumentTemplateResource,
                                        human_name='Document template',
                                        short_description='Select a document template')
    })

    config_specs: ConfigSpecs = {
        'document_template': DocumentTemplateParam(),
    }

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        document_template: DocumentTemplate = params['document_template']
        return {
            'document_template': DocumentTemplateResource(document_template_id=document_template.id)
        }
