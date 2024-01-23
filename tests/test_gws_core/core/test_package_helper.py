# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import os
from unittest import TestCase

from pandas import DataFrame

from gws_core import PackageHelper as pkg
from gws_core import Text


# test_package_helper
class TestPackageHelper(TestCase):

    def test_package_load(self):
        self.assertTrue(pkg.module_exists("pandas"))

        # programmatically load a existing module
        module = pkg.load_module("pandas")
        data = module.DataFrame()
        self.assertTrue(isinstance(data, DataFrame))

        # programmatically load a module from a file
        cdir = os.path.dirname(os.path.abspath(__file__))
        module = pkg.load_module_from_file(os.path.join(cdir, "local_module", "hello_module.py"))
        hello = module.Hello()
        text = hello.say_hello()
        self.assertTrue(isinstance(text, Text))
        self.assertTrue(text.get_data(), "hello")

    def test_package_install(self):
        self.assertFalse(pkg.module_exists("clean-text"))

        # programmatically install new package
        pkg.install("clean-text")
        cleantext = pkg.load_module("cleantext")
        self.assertTrue(pkg.module_exists("cleantext"))

        # import cleantext
        text = cleantext.clean("école")
        self.assertEqual(text, "ecole")

        pkg.uninstall("clean-text")
        self.assertFalse(pkg.module_exists("clean-text"))
