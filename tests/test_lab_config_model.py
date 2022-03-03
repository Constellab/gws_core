# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import List

from gws_core.brick.brick_dto import BrickVersion
from gws_core.lab.lab_config_model import LabConfigModel
from gws_core.test.base_test_case import BaseTestCase


class TestLabConfig(BaseTestCase):

    def test_lab_config_model(self):
        count = LabConfigModel.select().count()
        self.assertEqual(count, 1)

        brick_versions: List[BrickVersion] = [
            {'name': 'test', 'version': '2.1.1'},
            {'name': 'gws_core', 'version': '1.1.1'}]
        LabConfigModel.create_config_if_not_exits(brick_versions)

        count = LabConfigModel.select().count()
        self.assertEqual(count, 2)

        # Try recreate the same config, it sould not create a new
        LabConfigModel.create_config_if_not_exits(brick_versions)
        count = LabConfigModel.select().count()
        self.assertEqual(count, 2)

        # Update gws_core
        brick_versions = [{'name': 'gws_core', 'version': '1.1.2'}, {'name': 'test', 'version': '2.1.1'}]
        LabConfigModel.create_config_if_not_exits(brick_versions)
        count = LabConfigModel.select().count()
        self.assertEqual(count, 3)
