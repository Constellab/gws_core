# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from gws_core import BaseTestCase
from gws_core.brick.technical_doc_service import TechnicalDocService


# test_technical_doc
class TestTechnicalDoc(BaseTestCase):

    def test_technical_doc(self):
        dict_ = TechnicalDocService.generate_technical_doc('gws_core')

        self.assertIsNotNone(dict_['resources'])
        self.assertIsNotNone(dict_['tasks'])
