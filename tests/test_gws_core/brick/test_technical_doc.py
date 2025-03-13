from gws_core.brick.technical_doc_service import TechnicalDocService
from gws_core.test.base_test_case import BaseTestCase


# test_technical_doc
class TestTechnicalDoc(BaseTestCase):

    def test_technical_doc(self):
        tech_doc = TechnicalDocService.generate_technical_doc('gws_core')
        self.assertIsNotNone(tech_doc)
        self.assertEqual(tech_doc.brick_name, 'gws_core')
        self.assertIsNotNone(tech_doc.resources)
        self.assertIsNotNone(tech_doc.tasks)
        self.assertIsNotNone(tech_doc.protocols)
        self.assertIsNotNone(tech_doc.other_classes)

    def test_text_technical_doc(self):

        result = TechnicalDocService.generate_tasks_technical_doc_as_md('gws_core')
        self.assertTrue(len(result) > 0)

        result = TechnicalDocService.generate_protocols_technical_doc_as_md('gws_core')
        self.assertTrue(len(result) > 0)

        result = TechnicalDocService.generate_resources_technical_doc_as_md('gws_core')
        self.assertTrue(len(result) > 0)
