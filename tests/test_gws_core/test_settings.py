# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from unittest import TestCase

from gws_core.core.utils.settings import Settings
from gws_core.lab.system_dto import SettingsDTO


# test_settings
class TestSettings(TestCase):

    def test_var(self):
        self.assertFalse(Settings.is_prod_mode())
        self.assertTrue(Settings.is_dev_mode())
        self.assertTrue(Settings.get_instance().is_test)

    def test_pip_packages(self):
        settings = Settings.get_instance()

        pandas = settings.get_pip_package("pandas")
        self.assertEqual(pandas.name, "pandas")
        self.assertTrue(pandas.version and pandas.version != "")

        multiple_packages = settings.get_pip_packages(["pandas", "numpy"])
        self.assertEqual(len(multiple_packages), 2)

    def test_to_json(self):
        self.assertIsInstance(Settings.get_instance().to_dto(), SettingsDTO)
