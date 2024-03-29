

from gws_core import BaseTestCase
from gws_core.brick.technical_doc_service import TechnicalDocService


# test_technical_doc
class TestTechnicalDoc(BaseTestCase):

    def test_technical_doc(self):
        technical_doc = TechnicalDocService.generate_technical_doc('gws_core')

        self.assertTrue(technical_doc.brick_name == 'gws_core')
        self.assertTrue(len(technical_doc.resources) > 0)
        self.assertTrue(len(technical_doc.tasks) > 0)
        self.assertTrue(len(technical_doc.protocols) > 0)
