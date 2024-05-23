from gws_core.brick.brick_model import BrickModel
from gws_core.brick.technical_doc_service import TechnicalDocService
from gws_core.test.base_test_case import BaseTestCase



class TestTechnicalDoc(BaseTestCase):

    def test_technical_doc(self):
        techDoc = TechnicalDocService.generate_technical_doc('gws_core')
        self.assertIsNotNone(techDoc)
        self.assertEqual(techDoc.brick_name, 'gws_core')
        self.assertIsNotNone(techDoc.resources)
        self.assertIsNotNone(techDoc.tasks)
        self.assertIsNotNone(techDoc.protocols)
        self.assertIsNotNone(techDoc.other_classes)