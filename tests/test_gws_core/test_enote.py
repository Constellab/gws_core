

from PIL import Image

from gws_core.core.utils.settings import Settings
from gws_core.document_template.document_template import DocumentTemplate
from gws_core.impl.enote.create_enote import CreateENote
from gws_core.impl.enote.enote_resource import ENoteResource
from gws_core.impl.enote.generate_report_from_enote import \
    GenerateReportFromENote
from gws_core.impl.enote.merge_enotes import MergeENotes
from gws_core.impl.enote.update_enote import UpdatENote
from gws_core.impl.file.file import File
from gws_core.impl.rich_text.rich_text import RichText
from gws_core.impl.rich_text.rich_text_file_service import (
    RichTextFileService, RichTextObjectType, RichTextUploadFileResultDTO)
from gws_core.impl.rich_text.rich_text_types import (RichTextBlockType,
                                                     RichTextFigureData)
from gws_core.impl.robot.robot_resource import Robot
from gws_core.io.io_spec import InputSpec
from gws_core.io.io_specs import InputSpecs
from gws_core.report.report import Report
from gws_core.report.task.report_resource import ReportResource
from gws_core.resource.resource import Resource
from gws_core.resource.resource_dto import ResourceOrigin
from gws_core.resource.resource_model import ResourceModel
from gws_core.resource.resource_set.resource_list import ResourceList
from gws_core.task.task_runner import TaskRunner
from gws_core.test.base_test_case import BaseTestCase


# test_enote
class TestEnote(BaseTestCase):

    def test_create_methods(self):
        enote = ENoteResource()
        enote.add_paragraph("This is a test paragraph")
        self.assertEqual(enote.get_block_at_index(0).type, RichTextBlockType.PARAGRAPH)

    def test_create_enote(self):
        rich_text = RichText()
        rich_text.add_paragraph("This is a test paragraph")

        task_runner = TaskRunner(CreateENote, {
            "title": "My custom note",
            "enote": rich_text.serialize()
        })

        outputs = task_runner.run()

        enote: ENoteResource = outputs['enote']
        self.assertIsInstance(enote, ENoteResource)
        self.assertEqual(enote.title, "My custom note")
        self.assertEqual(enote.get_block_at_index(0).type, RichTextBlockType.PARAGRAPH)
        self.assertEqual(enote.get_block_at_index(0).data["text"], "This is a test paragraph")

    def test_create_enote_from_template(self):

        doc_template = DocumentTemplate(title="My template")
        template_rich_text = RichText()
        template_rich_text.add_paragraph("This is a test paragraph")

        # add figure to the template
        figure_data = self._create_document_template_image(doc_template.id, 'test')
        template_rich_text.add_figure(figure_data)

        file_data = self._create_document_template_file(doc_template.id, 'hello.txt')
        template_rich_text.add_file(file_data)

        doc_template.content = template_rich_text.get_content()
        doc_template.save()

        # Test create e-note from template
        task_runner = TaskRunner(CreateENote, params={
            "title": "",
            "template": doc_template.id,
        })

        outputs = task_runner.run()

        enote: ENoteResource = outputs['enote']
        self.assertIsInstance(enote, ENoteResource)
        self.assertEqual(enote.title, "My template")
        self.assertEqual(enote.get_block_at_index(0).type, RichTextBlockType.PARAGRAPH)
        self.assertEqual(enote.get_block_at_index(0).data["text"], "This is a test paragraph")

        # check that the image exists
        self.assertEqual(enote.get_block_at_index(1).type, RichTextBlockType.FIGURE)
        self.assertEqual(enote.get_block_at_index(1).data['title'], 'test')

        # check that the file exists
        self.assertEqual(enote.get_block_at_index(2).type, RichTextBlockType.FILE)
        self.assertEqual(enote.get_block_at_index(2).data['name'], 'hello.txt')

        # the enote should have 2 resources (1 for the figure, 1 for the file)
        self.assertEqual(len(enote.get_resources()), 2)

    def test_update_enote(self):
        base_enote = ENoteResource(title="My custom note")
        base_enote.add_paragraph("This is a test paragraph")

        # Test update e-note
        rich_text = RichText()
        rich_text.add_paragraph("This is a new paragraph")

        task_runner = TaskRunner(UpdatENote, params={
            "section-title": "New section",
            "enote": rich_text.serialize()
        }, inputs={
            "enote": base_enote
        })

        outputs = task_runner.run()
        updated_enote: ENoteResource = outputs['enote']
        self.assertIsInstance(updated_enote, ENoteResource)
        self.assertEqual(updated_enote.title, "My custom note")
        self.assertEqual(updated_enote.get_block_at_index(0).type, RichTextBlockType.PARAGRAPH)
        self.assertEqual(updated_enote.get_block_at_index(0).data["text"], "This is a test paragraph")
        self.assertEqual(updated_enote.get_block_at_index(1).type, RichTextBlockType.HEADER)
        self.assertEqual(updated_enote.get_block_at_index(1).data["text"], "New section")
        self.assertEqual(updated_enote.get_block_at_index(2).type, RichTextBlockType.PARAGRAPH)
        self.assertEqual(updated_enote.get_block_at_index(2).data["text"], "This is a new paragraph")

    def test_generate_report_from_enote(self):
        enote = ENoteResource(title="My custom note")
        enote.add_paragraph("This is a test paragraph")
        enote.add_figure_file(self._create_enote_image(), title='test', create_new_resource=False)
        enote.add_default_view_from_resource(self._create_resource(), title='view', create_new_resource=False)

        # add a view from a resource that is not saved
        robot = Robot.empty()
        enote.add_default_view_from_resource(robot, title='view', create_new_resource=True)

        # Test generate report from e-note
        task_runner = TaskRunner(GenerateReportFromENote, inputs={
            "enote": enote
        })

        outputs = task_runner.run()

        report: ReportResource = outputs['report']
        self.assertIsInstance(report, ReportResource)
        self.assertEqual(report.get_content().get_block_at_index(0).type, RichTextBlockType.PARAGRAPH)
        self.assertEqual(report.get_content().get_block_at_index(0).data["text"], "This is a test paragraph")
        self.assertEqual(report.get_content().get_block_at_index(1).type, RichTextBlockType.FIGURE)
        # the first view was attached to a resource, it should generate a RESOURCE_VIEW
        self.assertEqual(report.get_content().get_block_at_index(2).type, RichTextBlockType.RESOURCE_VIEW)
        # the second view was not attached to a resource, it should generate a FILE_VIEW
        self.assertEqual(report.get_content().get_block_at_index(3).type, RichTextBlockType.FILE_VIEW)

        report_db = Report.get_by_id_and_check(report.report_id)
        self.assertIsNotNone(report_db)

    def test_merge_enote(self):
        # Test merge enote
        first_enote = ENoteResource(title="First e-note")
        first_enote.add_paragraph("This is a first paragraph")

        second_enote = ENoteResource(title="Second e-note")
        second_enote.add_paragraph("This is a second paragraph")
        second_enote.add_figure_file(self._create_enote_image(), title='figure', create_new_resource=False)
        second_enote.add_default_view_from_resource(self._create_resource(), title='view', create_new_resource=False)

        resource_list = ResourceList([first_enote, second_enote])
        task_runner = TaskRunner(MergeENotes, params={
            "title": "Merged enote",
        }, inputs={
            "source": resource_list
        },
            # need to override this to make dynamic io work
            input_specs=InputSpecs({
                "source": InputSpec(ResourceList),
            }),)

        outputs = task_runner.run()

        merged_enote: ENoteResource = outputs['enote']
        self.assertIsInstance(merged_enote, ENoteResource)
        self.assertEqual(merged_enote.title, "Merged enote")
        self.assertEqual(merged_enote.get_block_at_index(0).type, RichTextBlockType.PARAGRAPH)
        self.assertEqual(merged_enote.get_block_at_index(0).data["text"], "This is a first paragraph")
        self.assertEqual(merged_enote.get_block_at_index(1).type, RichTextBlockType.PARAGRAPH)
        self.assertEqual(merged_enote.get_block_at_index(1).data["text"], "This is a second paragraph")
        self.assertEqual(merged_enote.get_block_at_index(2).type, RichTextBlockType.FIGURE)
        self.assertEqual(merged_enote.get_block_at_index(2).data['title'], 'figure')
        self.assertEqual(merged_enote.get_block_at_index(3).type, RichTextBlockType.ENOTE_VIEW)
        self.assertEqual(merged_enote.get_block_at_index(3).data['title'], 'view')

        # the merged enote contains the figure and view resources
        self.assertEqual(len(merged_enote.get_resources()), 2)

    def _create_image(self) -> Image.Image:
        img = Image.new('RGB', (1, 1))
        img.putdata([(255, 0, 0)])
        return img

    def _create_enote_image(self) -> File:
        # create an image with a red pixel and save it to a file
        img = self._create_image()

        temp_dir = Settings.make_temp_dir()
        filename = f"{temp_dir}/temp.png"
        img.save(filename)

        return File(filename)

    def _create_document_template_image(self, document_template_id: str, title: str = None) -> RichTextFigureData:
        # create an image with a red pixel and save it in report storage
        img = self._create_image()

        # add the image to the template
        result = RichTextFileService.save_image(RichTextObjectType.DOCUMENT_TEMPLATE, document_template_id, img, 'png')
        return {
            "filename": result.filename,
            "width": result.width,
            "height": result.height,
            "naturalHeight": result.height,
            "naturalWidth": result.width,
            "title": title,
            "caption": None,
        }

    def _create_document_template_file(
            self, document_template_id: str, filename: str = None) -> RichTextUploadFileResultDTO:
        # write the file
        return RichTextFileService.write_file(
            RichTextObjectType.DOCUMENT_TEMPLATE, document_template_id, 'hello', filename, 'w')

    def _create_resource(self) -> Resource:
        resource_model = ResourceModel.save_from_resource(Robot.empty(), ResourceOrigin.UPLOADED)

        return resource_model.get_resource(new_instance=True)
