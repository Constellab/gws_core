import os
from unittest import TestCase
from unittest.mock import patch

from gws_core.core.utils.settings import Settings
from gws_core.core.utils.settings_dto import SettingsDTO


# test_settings
class TestSettings(TestCase):
    def test_var(self):
        self.assertFalse(Settings.is_prod_mode())
        self.assertTrue(Settings.is_dev_mode())
        self.assertTrue(Settings.get_instance().is_test)

    def test_is_mcp_server_enabled(self):
        env_var = Settings.MCP_SERVER_ENABLED_ENV_VAR

        # Default OFF when unset.
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop(env_var, None)
            self.assertFalse(Settings.is_mcp_server_enabled())

        # Only the exact string "true" enables it.
        with patch.dict(os.environ, {env_var: "true"}):
            self.assertTrue(Settings.is_mcp_server_enabled())

        for value in ("false", "1", "TRUE", "yes", ""):
            with patch.dict(os.environ, {env_var: value}):
                self.assertFalse(Settings.is_mcp_server_enabled())

    def test_pip_packages(self):
        settings = Settings.get_instance()

        pandas = settings.get_pip_package("pandas")
        assert pandas is not None
        self.assertEqual(pandas.name, "pandas")
        self.assertTrue(pandas.version and pandas.version != "")

        multiple_packages = settings.get_pip_packages(["pandas", "numpy"])
        self.assertEqual(len(multiple_packages), 2)

    def test_to_json(self):
        self.assertIsInstance(Settings.get_instance().to_dto(), SettingsDTO)
