# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from time import sleep

from gws_core.test.base_test_case import BaseTestCase
from gws_core.user.activity.activity_dto import (ActivityObjectType,
                                                 ActivityType)
from gws_core.user.activity.activity_service import ActivityService


# test_activity
class TestActivity(BaseTestCase):

    def test_activity(self):

        ActivityService.add(
            ActivityType.CREATE, object_type=ActivityObjectType.EXPERIMENT, object_id="test")

        sleep(1.5)

        ActivityService.add(
            ActivityType.DELETE, object_type=ActivityObjectType.EXPERIMENT, object_id="test")

        last_activity = ActivityService.get_last_activity()

        self.assertIsNotNone(last_activity)
        self.assertEqual(last_activity.activity_type, ActivityType.DELETE)
        self.assertEqual(last_activity.object_type, ActivityObjectType.EXPERIMENT)
        self.assertEqual(last_activity.object_id, "test")
        self.assertIsNotNone(last_activity.user)
        self.assertIsNotNone(last_activity.to_dto())

        sleep(1.5)
        # test add_or_update
        activity = ActivityService.add_or_update(
            ActivityType.DELETE, object_type=ActivityObjectType.EXPERIMENT, object_id="test")

        # this should have been updated
        self.assertEqual(activity.id, last_activity.id)
        self.assertNotEqual(activity.last_modified_at, last_activity.last_modified_at)

        # test add_or_update with other object_id
        activity = ActivityService.add_or_update(
            ActivityType.DELETE, object_type=ActivityObjectType.EXPERIMENT, object_id="test2")

        # this should have been created
        self.assertNotEqual(activity.id, last_activity.id)
