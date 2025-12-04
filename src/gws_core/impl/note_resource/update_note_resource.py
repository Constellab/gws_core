from gws_core.config.config_params import ConfigParams
from gws_core.config.config_specs import ConfigSpecs
from gws_core.config.param.param_spec import StrParam
from gws_core.impl.rich_text.block.rich_text_block_header import RichTextBlockHeaderLevel
from gws_core.impl.rich_text.rich_text import RichText
from gws_core.impl.rich_text.rich_text_param import RichTextParam
from gws_core.io.io_spec import InputSpec, OutputSpec
from gws_core.io.io_specs import InputSpecs, OutputSpecs
from gws_core.task.task import Task
from gws_core.task.task_decorator import task_decorator
from gws_core.task.task_io import TaskInputs, TaskOutputs

from .note_resource import NoteResource


@task_decorator(
    unique_name="UpdatNoteResource",
    human_name="Update note resource",
    short_description="Append content to an existing note resource",
)
class UpdatNoteResource(Task):
    """
    Append the content provided in the configuration to the input note resource.
    """

    input_specs: InputSpecs = InputSpecs(
        {"note": InputSpec(NoteResource, human_name="Note resource")}
    )

    output_specs: OutputSpecs = OutputSpecs(
        {"note": OutputSpec(NoteResource, human_name="Note resource")}
    )

    config_specs = ConfigSpecs(
        {
            "section-title": StrParam(
                optional=True,
                human_name="Section title",
                short_description="Title of the new section",
            ),
            "note": RichTextParam(
                human_name="Note resource",
                short_description="Content to append to the input note resource",
            ),
        }
    )

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        note_resource: NoteResource = inputs["note"]
        section_title: str = params["section-title"]
        note_param: RichText = params["note"]

        if section_title is not None:
            note_resource.add_header(section_title, RichTextBlockHeaderLevel.HEADER_1)

        note_resource.append_basic_rich_text(note_param)

        return {"note": note_resource}
