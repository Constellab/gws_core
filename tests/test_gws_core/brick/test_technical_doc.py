from gws_core.brick.technical_doc_service import TechnicalDocService
from gws_core.test.base_test_case import BaseTestCase


class TestTechnicalDoc(BaseTestCase):

    def test_technical_doc(self):
        tech_doc = TechnicalDocService.generate_technical_doc('gws_core')
        self.assertIsNotNone(tech_doc)
        self.assertEqual(tech_doc.brick_name, 'gws_core')
        self.assertIsNotNone(tech_doc.resources)
        self.assertIsNotNone(tech_doc.tasks)
        self.assertIsNotNone(tech_doc.protocols)
        self.assertIsNotNone(tech_doc.other_classes)
