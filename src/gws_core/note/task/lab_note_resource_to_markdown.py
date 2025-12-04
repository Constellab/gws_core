import os
from typing import cast

from gws_core.config.config_params import ConfigParams
from gws_core.impl.file.file import File
from gws_core.io.io_spec import InputSpec, OutputSpec
from gws_core.io.io_specs import InputSpecs, OutputSpecs
from gws_core.note.task.lab_note_resource import LabNoteResource
from gws_core.task.task import Task
from gws_core.task.task_decorator import task_decorator
from gws_core.task.task_io import TaskInputs, TaskOutputs


@task_decorator(
    "LabNoteResourceToMarkdown",
    human_name="Convert lab note resource to markdown",
    short_description="Convert a lab note resource to markdown file",
)
class LabNoteResourceToMarkdown(Task):
    """
    Convert a lab note resource to markdown file.

    Note: the images are not converted to markdown.
    """

    input_specs: InputSpecs = InputSpecs(
        {
            "note": InputSpec(
                LabNoteResource,
                human_name="Lab note resource",
                short_description="Note resource to convert",
            )
        }
    )

    output_specs: OutputSpecs = OutputSpecs(
        {
            "markdown": OutputSpec(
                File,
                human_name="Markdown file",
                short_description="Markdown file with the note content",
            ),
        }
    )

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        note_resource = cast(LabNoteResource, inputs["note"])

        tmp_dir = self.create_tmp_dir()

        file_path = os.path.join(tmp_dir, f"{note_resource.get_note().title}.md")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(note_resource.to_markdown())

        return {"markdown": File(file_path)}
