# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from time import sleep

from gws_core.test.base_test_case import BaseTestCase
from gws_core.user.activity import Activity
from gws_core.user.activity_service import ActivityService


# test_activity
class TestActivity(BaseTestCase):

    def test_activity(self):

        last_activity = ActivityService.get_last_activity()

        self.assertIsNone(last_activity)

        ActivityService.add(
            Activity.CREATE, object_type="test", object_id="test")

        sleep(1.5)

        ActivityService.add(
            Activity.UPDATE, object_type="test", object_id="test")

        last_activity = ActivityService.get_last_activity()

        self.assertIsNotNone(last_activity)
        self.assertEqual(last_activity.activity_type, Activity.UPDATE)
        self.assertEqual(last_activity.object_type, "test")
        self.assertEqual(last_activity.object_id, "test")
        self.assertIsNotNone(last_activity.user)
        self.assertIsNotNone(last_activity.to_json())
