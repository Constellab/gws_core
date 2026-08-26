import os
from unittest import TestCase

from gws_core import PackageHelper, Text
from pandas import DataFrame


# test_package_helper
class TestPackageHelper(TestCase):
    def test_package_load(self):
        self.assertTrue(PackageHelper.module_exists("pandas"))

        # programmatically load a existing module
        module = PackageHelper.load_module("pandas")
        data = module.DataFrame()
        self.assertTrue(isinstance(data, DataFrame))

        # programmatically load a module from a file
        cdir = os.path.dirname(os.path.abspath(__file__))
        module = PackageHelper.load_module_from_file(os.path.join(cdir, "local_module", "hello_module.py"))
        hello = module.Hello()
        text = hello.say_hello()
        self.assertTrue(isinstance(text, Text))
        self.assertTrue(text.get_data(), "hello")

    def test_package_install(self):
        self.assertFalse(PackageHelper.module_exists("clean-text"))

        # programmatically install new package
        PackageHelper.install("clean-text")
        cleantext = PackageHelper.load_module("cleantext")
        self.assertTrue(PackageHelper.module_exists("cleantext"))

        # import cleantext
        text = cleantext.clean("école")
        self.assertEqual(text, "ecole")

        PackageHelper.uninstall("clean-text")
        self.assertFalse(PackageHelper.module_exists("clean-text"))
