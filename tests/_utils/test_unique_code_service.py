

from time import sleep
from unittest import TestCase

from gws_core.user.unique_code_service import (CodeObject,
                                               InvalidUniqueCodeException,
                                               UniqueCodeService)


class TestUniqueCodeService(TestCase):

    def test_unique_code(self):
        code = UniqueCodeService.generate_code('0', {'obj': 'top'}, 1000)

        result: CodeObject = UniqueCodeService.check_code(code)

        self.assertEqual(result['user_id'], '0')
        self.assertEqual(result['obj'], {'obj': 'top'})

        with self.assertRaises(InvalidUniqueCodeException):
            UniqueCodeService.check_code(code)

        with self.assertRaises(InvalidUniqueCodeException):
            UniqueCodeService.check_code('code')

        # check if experation date is working
        code = UniqueCodeService.generate_code('0', {'obj': 'top'}, 1)
        sleep(2)

        with self.assertRaises(InvalidUniqueCodeException):
            UniqueCodeService.check_code(code)
