from typing import List

from gws_core.brick.brick_dto import BrickVersion
from gws_core.lab.lab_config_model import LabConfigModel
from gws_core.test.base_test_case import BaseTestCase


# test_lab_config_model
class TestLabConfig(BaseTestCase):
    def test_lab_config_model(self):
        count = LabConfigModel.select().count()
        self.assertEqual(count, 1)

        brick_versions = [
            BrickVersion(name="test", version="2.1.1"),
            BrickVersion(name="gws_core", version="1.1.1"),
        ]
        config_1 = LabConfigModel.create_config_if_not_exits(brick_versions)

        count = LabConfigModel.select().count()
        self.assertEqual(count, 2)

        # Try recreate the same config, it sould not create a new
        same_config_2 = LabConfigModel.create_config_if_not_exits(brick_versions)
        count = LabConfigModel.select().count()
        self.assertEqual(count, 2)

        # Update gws_core
        brick_versions = [
            BrickVersion(name="gws_core", version="1.1.2"),
            BrickVersion(name="test", version="2.1.1"),
        ]
        config_2 = LabConfigModel.create_config_if_not_exits(brick_versions)
        count = LabConfigModel.select().count()
        self.assertEqual(count, 3)

        # Check compatibility
        self.assertTrue(config_1.is_compatible_with(same_config_2))
        self.assertFalse(config_1.is_compatible_with(config_2))
