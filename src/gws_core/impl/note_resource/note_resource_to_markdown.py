

import os
from typing import cast

from gws_core.config.config_params import ConfigParams
from gws_core.impl.file.file import File
from gws_core.io.io_spec import InputSpec, OutputSpec
from gws_core.io.io_specs import InputSpecs, OutputSpecs
from gws_core.task.task import Task
from gws_core.task.task_decorator import task_decorator
from gws_core.task.task_io import TaskInputs, TaskOutputs

from .note_resource import NoteResource


@task_decorator("NoteResourceToMarkdown", human_name="Convert note resource to markdown",
                short_description="Convert a note resource to markdown file")
class NoteResourceToMarkdown(Task):
    """
    Convert a note resource to markdown file.

    Note: the images are not converted to markdown.
    """

    input_specs: InputSpecs = InputSpecs({
        'note': InputSpec(NoteResource, human_name='Note resource', short_description='Note resource to convert')
    })

    output_specs: OutputSpecs = OutputSpecs({'markdown': OutputSpec(
        File, human_name='Markdown file', short_description='Markdown file with the note content'), })

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        note_resource = cast(NoteResource, inputs['note'])

        tmp_dir = self.create_tmp_dir()

        file_path = os.path.join(tmp_dir, f"{note_resource.title}.md")
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(note_resource.to_markdown())

        return {
            'markdown': File(file_path)
        }
