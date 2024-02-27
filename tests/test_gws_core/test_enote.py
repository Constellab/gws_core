# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from gws_core.impl.enote.create_enote import CreateENote
from gws_core.impl.enote.enote_resource import ENoteResource
from gws_core.impl.enote.generate_report_from_enote import \
    GenerateReportFromENote
from gws_core.impl.enote.merge_enotes import MergeENotes
from gws_core.impl.enote.update_enote import UpdatENote
from gws_core.impl.rich_text.rich_text import RichText
from gws_core.impl.rich_text.rich_text_types import RichTextBlockType
from gws_core.io.io_spec import InputSpec
from gws_core.io.io_specs import InputSpecs
from gws_core.report.report import Report
from gws_core.report.task.report_resource import ReportResource
from gws_core.report.template.report_template import ReportTemplate
from gws_core.resource.resource_set.resource_list import ResourceList
from gws_core.task.task_runner import TaskRunner
from gws_core.test.base_test_case import BaseTestCase


# test_enote
class TestEnote(BaseTestCase):

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
        self.assertEqual(enote.rich_text.get_block_at_index(0).type, RichTextBlockType.PARAGRAPH)
        self.assertEqual(enote.rich_text.get_block_at_index(0).data["text"], "This is a test paragraph")

    def test_create_enote_from_template(self):
        template_rich_text = RichText()
        template_rich_text.add_paragraph("This is a test paragraph")

        report_template = ReportTemplate(title="My template", content=template_rich_text.get_content())
        report_template.save()

        # Test create e-note from template
        task_runner = TaskRunner(CreateENote, params={
            "title": "",
            "template": report_template.id,
        })

        outputs = task_runner.run()

        enote: ENoteResource = outputs['enote']
        self.assertIsInstance(enote, ENoteResource)
        self.assertEqual(enote.title, "My template")
        self.assertEqual(enote.rich_text.get_block_at_index(0).type, RichTextBlockType.PARAGRAPH)
        self.assertEqual(enote.rich_text.get_block_at_index(0).data["text"], "This is a test paragraph")

    def test_update_enote(self):
        base_rich_text = RichText()
        base_rich_text.add_paragraph("This is a test paragraph")
        base_enote = ENoteResource(title="My custom note", rich_text=base_rich_text)

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
        self.assertEqual(updated_enote.rich_text.get_block_at_index(0).type, RichTextBlockType.PARAGRAPH)
        self.assertEqual(updated_enote.rich_text.get_block_at_index(0).data["text"], "This is a test paragraph")
        self.assertEqual(updated_enote.rich_text.get_block_at_index(1).type, RichTextBlockType.HEADER)
        self.assertEqual(updated_enote.rich_text.get_block_at_index(1).data["text"], "New section")
        self.assertEqual(updated_enote.rich_text.get_block_at_index(2).type, RichTextBlockType.PARAGRAPH)
        self.assertEqual(updated_enote.rich_text.get_block_at_index(2).data["text"], "This is a new paragraph")

    def test_generate_report_from_enote(self):
        rich_text = RichText()
        rich_text.add_paragraph("This is a test paragraph")
        enote = ENoteResource(title="My custom note", rich_text=rich_text)

        # Test generate report from e-note
        task_runner = TaskRunner(GenerateReportFromENote, inputs={
            "enote": enote
        })

        outputs = task_runner.run()

        report: ReportResource = outputs['report']
        self.assertIsInstance(report, ReportResource)
        self.assertEqual(report.get_content().get_block_at_index(0).type, RichTextBlockType.PARAGRAPH)
        self.assertEqual(report.get_content().get_block_at_index(0).data["text"], "This is a test paragraph")

        report_db = Report.get_by_id_and_check(report.report_id)
        self.assertIsNotNone(report_db)

    def test_merge_enote(self):
        # Test merge enote
        first_enote = ENoteResource(title="First e-note", rich_text=RichText())
        first_enote.add_paragraph("This is a first paragraph")
        second_enote = ENoteResource(title="Second e-note", rich_text=RichText())
        second_enote.add_paragraph("This is a second paragraph")
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
        self.assertEqual(merged_enote.rich_text.get_block_at_index(0).type, RichTextBlockType.PARAGRAPH)
        self.assertEqual(merged_enote.rich_text.get_block_at_index(0).data["text"], "This is a first paragraph")
        self.assertEqual(merged_enote.rich_text.get_block_at_index(1).type, RichTextBlockType.PARAGRAPH)
        self.assertEqual(merged_enote.rich_text.get_block_at_index(1).data["text"], "This is a second paragraph")
