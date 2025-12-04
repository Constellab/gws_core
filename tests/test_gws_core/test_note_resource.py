from typing import cast

from PIL import Image

from gws_core.core.utils.settings import Settings
from gws_core.impl.file.file import File
from gws_core.impl.note_resource.create_note_resource import CreateNoteResource
from gws_core.impl.note_resource.generate_lab_note import GenerateLabNote
from gws_core.impl.note_resource.merge_notes_resource import MergeNoteResources
from gws_core.impl.note_resource.note_resource import NoteResource
from gws_core.impl.note_resource.update_note_resource import UpdatNoteResource
from gws_core.impl.rich_text.block.rich_text_block import RichTextBlockType
from gws_core.impl.rich_text.block.rich_text_block_figure import RichTextBlockFigure
from gws_core.impl.rich_text.block.rich_text_block_file import RichTextBlockFile
from gws_core.impl.rich_text.block.rich_text_block_header import RichTextBlockHeader
from gws_core.impl.rich_text.block.rich_text_block_paragraph import RichTextBlockParagraph
from gws_core.impl.rich_text.block.rich_text_block_view import RichTextBlockNoteResourceView
from gws_core.impl.rich_text.rich_text import RichText
from gws_core.impl.rich_text.rich_text_file_service import (
    RichTextFileService,
    RichTextUploadFileResultDTO,
)
from gws_core.impl.rich_text.rich_text_types import RichTextObjectType
from gws_core.impl.robot.robot_resource import Robot
from gws_core.io.io_spec import InputSpec
from gws_core.io.io_specs import InputSpecs
from gws_core.note.note import Note
from gws_core.note.task.lab_note_resource import LabNoteResource
from gws_core.note_template.note_template import NoteTemplate
from gws_core.resource.resource import Resource
from gws_core.resource.resource_dto import ResourceOrigin
from gws_core.resource.resource_model import ResourceModel
from gws_core.resource.resource_set.resource_list import ResourceList
from gws_core.task.task_runner import TaskRunner
from gws_core.test.base_test_case import BaseTestCase


# test_note_resource
class TestNoteResource(BaseTestCase):
    def test_create_methods(self):
        note = NoteResource()
        note.add_paragraph("This is a test paragraph")
        self.assertEqual(note.get_block_at_index(0).type, RichTextBlockType.PARAGRAPH)

    def test_create_note(self):
        rich_text = RichText()
        rich_text.add_paragraph("This is a test paragraph")

        task_runner = TaskRunner(
            CreateNoteResource, {"title": "My custom note", "note": rich_text.serialize()}
        )

        outputs = task_runner.run()

        note = cast(NoteResource, outputs["note"])
        self.assertIsInstance(note, NoteResource)
        self.assertEqual(note.title, "My custom note")
        block_data = cast(RichTextBlockParagraph, note.get_block_at_index(0).get_data())
        self.assertIsInstance(block_data, RichTextBlockParagraph)
        self.assertEqual(block_data.text, "This is a test paragraph")

    def test_create_note_from_template(self):
        doc_template = NoteTemplate(title="My template")
        template_rich_text = RichText()
        template_rich_text.add_paragraph("This is a test paragraph")

        # add figure to the template
        figure_data = self._create_note_template_image(doc_template.id, "test")
        template_rich_text.add_figure(figure_data)

        file_data = self._create_note_template_file(doc_template.id, "hello.txt")
        template_rich_text.add_file(file_data)

        doc_template.content = template_rich_text.to_dto()
        doc_template.save()

        # Test create note resource from template
        task_runner = TaskRunner(
            CreateNoteResource,
            params={
                "title": "",
                "template": doc_template.id,
            },
        )

        outputs = task_runner.run()

        note = cast(NoteResource, outputs["note"])
        self.assertIsInstance(note, NoteResource)
        self.assertEqual(note.title, "My template")
        block_data = cast(RichTextBlockParagraph, note.get_block_at_index(0).get_data())
        self.assertIsInstance(block_data, RichTextBlockParagraph)
        self.assertEqual(block_data.text, "This is a test paragraph")

        # check that the image exists
        figure_block = cast(RichTextBlockFigure, note.get_block_at_index(1).get_data())
        self.assertIsInstance(figure_block, RichTextBlockFigure)
        self.assertEqual(figure_block.title, "test")

        # check that the file exists
        file_block = cast(RichTextBlockFile, note.get_block_at_index(2).get_data())
        self.assertIsInstance(file_block, RichTextBlockFile)
        self.assertEqual(file_block.name, "hello.txt")

        # the note should have 2 resources (1 for the figure, 1 for the file)
        self.assertEqual(len(note.get_resources()), 2)

    def test_update_note(self):
        base_note = NoteResource(title="My custom note")
        base_note.add_paragraph("This is a test paragraph")

        # Test update note resource
        rich_text = RichText()
        rich_text.add_paragraph("This is a new paragraph")

        task_runner = TaskRunner(
            UpdatNoteResource,
            params={"section-title": "New section", "note": rich_text.serialize()},
            inputs={"note": base_note},
        )

        outputs = task_runner.run()
        updated_note = cast(NoteResource, outputs["note"])
        self.assertIsInstance(updated_note, NoteResource)
        self.assertEqual(updated_note.title, "My custom note")
        first_block = cast(RichTextBlockParagraph, updated_note.get_block_at_index(0).get_data())
        self.assertIsInstance(first_block, RichTextBlockParagraph)
        self.assertEqual(first_block.text, "This is a test paragraph")
        second_block = cast(RichTextBlockParagraph, updated_note.get_block_at_index(1).get_data())
        self.assertIsInstance(second_block, RichTextBlockHeader)
        self.assertEqual(second_block.text, "New section")
        third_block = cast(RichTextBlockParagraph, updated_note.get_block_at_index(2).get_data())
        self.assertIsInstance(third_block, RichTextBlockParagraph)
        self.assertEqual(third_block.text, "This is a new paragraph")

    def test_generate_note_from_note(self):
        note_resource = NoteResource(title="My custom note")
        note_resource.add_paragraph("This is a test paragraph")
        note_resource.add_figure_file(
            self._create_note_image(), title="test", create_new_resource=False
        )
        note_resource.add_default_view_from_resource(
            self._create_resource(), title="view", create_new_resource=False
        )

        # add a view from a resource that is not saved
        robot = Robot.empty()
        note_resource.add_default_view_from_resource(robot, title="view", create_new_resource=True)

        # Test generate note from note resource
        task_runner = TaskRunner(GenerateLabNote, inputs={"note": note_resource})

        outputs = task_runner.run()

        note = cast(LabNoteResource, outputs["note"])
        self.assertIsInstance(note, LabNoteResource)

        first_block = cast(
            RichTextBlockParagraph, note.get_content().get_block_at_index(0).get_data()
        )
        self.assertIsInstance(first_block, RichTextBlockParagraph)
        self.assertEqual(first_block.text, "This is a test paragraph")
        # the first view was attached to a resource, it should generate a RESOURCE_VIEW
        self.assertEqual(
            note.get_content().get_block_at_index(2).type, RichTextBlockType.RESOURCE_VIEW
        )
        # the second view was not attached to a resource, it should generate a FILE_VIEW
        self.assertEqual(note.get_content().get_block_at_index(3).type, RichTextBlockType.FILE_VIEW)

        note_db = Note.get_by_id_and_check(note.note_id)
        self.assertIsNotNone(note_db)

    def test_merge_note(self):
        # Test merge note
        first_note = NoteResource(title="First note resource")
        first_note.add_paragraph("This is a first paragraph")

        second_note = NoteResource(title="Second note resource")
        second_note.add_paragraph("This is a second paragraph")
        second_note.add_figure_file(
            self._create_note_image(), title="figure", create_new_resource=False
        )
        second_note.add_default_view_from_resource(
            self._create_resource(), title="view", create_new_resource=False
        )

        resource_list = ResourceList([first_note, second_note])
        task_runner = TaskRunner(
            MergeNoteResources,
            params={
                "title": "Merged note",
            },
            inputs={"source": resource_list},
            # need to override this to make dynamic io work
            input_specs=InputSpecs(
                {
                    "source": InputSpec(ResourceList),
                }
            ),
        )

        outputs = task_runner.run()

        merged_note = cast(NoteResource, outputs["note"])
        self.assertIsInstance(merged_note, NoteResource)
        self.assertEqual(merged_note.title, "Merged note")

        first_block = cast(RichTextBlockParagraph, merged_note.get_block_at_index(0).get_data())
        self.assertIsInstance(first_block, RichTextBlockParagraph)
        self.assertEqual(first_block.text, "This is a first paragraph")
        second_block = cast(RichTextBlockParagraph, merged_note.get_block_at_index(1).get_data())
        self.assertIsInstance(second_block, RichTextBlockParagraph)
        self.assertEqual(second_block.text, "This is a second paragraph")
        third_block = cast(RichTextBlockFigure, merged_note.get_block_at_index(2).get_data())
        self.assertIsInstance(third_block, RichTextBlockFigure)
        self.assertEqual(third_block.title, "figure")
        fourth_block = cast(
            RichTextBlockNoteResourceView, merged_note.get_block_at_index(3).get_data()
        )
        self.assertIsInstance(fourth_block, RichTextBlockNoteResourceView)
        self.assertEqual(fourth_block.title, "view")

        # the merged note contains the figure and view resources
        self.assertEqual(len(merged_note.get_resources()), 2)

    def _create_image(self) -> Image.Image:
        img = Image.new("RGB", (1, 1))
        img.putdata([(255, 0, 0)])
        return img

    def _create_note_image(self) -> File:
        # create an image with a red pixel and save it to a file
        img = self._create_image()

        temp_dir = Settings.make_temp_dir()
        filename = f"{temp_dir}/temp.png"
        img.save(filename)

        return File(filename)

    def _create_note_template_image(
        self, note_template_id: str, title: str = None
    ) -> RichTextBlockFigure:
        # create an image with a red pixel and save it in note storage
        img = self._create_image()

        # add the image to the template
        result = RichTextFileService.save_image(
            RichTextObjectType.NOTE_TEMPLATE, note_template_id, img, "png"
        )
        return RichTextBlockFigure(
            filename=result.filename,
            width=result.width,
            height=result.height,
            naturalHeight=result.height,
            naturalWidth=result.width,
            title=title,
            caption=None,
        )

    def _create_note_template_file(
        self, note_template_id: str, filename: str = None
    ) -> RichTextBlockFile:
        # write the file
        file = RichTextFileService.write_file(
            RichTextObjectType.NOTE_TEMPLATE, note_template_id, "hello", filename, "w"
        )

        return RichTextBlockFile(
            name=file.name,
            size=file.size,
        )

    def _create_resource(self) -> Resource:
        resource_model = ResourceModel.save_from_resource(Robot.empty(), ResourceOrigin.UPLOADED)

        return resource_model.get_resource(new_instance=True)
