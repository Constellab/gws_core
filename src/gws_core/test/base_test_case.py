

from ..scenario.queue_service import QueueService
from .base_test_case_light import BaseTestCaseLight
from .test_helper import TestHelper


class BaseTestCase(BaseTestCaseLight):
    """Base class for test, contain method to ease testing and automatically init env and clear it after
    Extend this class if your tests require database. If you are only using the TaskRunner, you can use BaseTestCaseComplete.
    This will init the database which is way slower.
    If you do not need the database, use BaseTestCaseLight
    """

    @classmethod
    def init_before_test(cls):
        TestHelper.delete_data_and_temp_folder()
        TestHelper.drop_tables()
        TestHelper.init_complete()

    @classmethod
    def clear_after_test(cls):
        QueueService.deinit()
        TestHelper.drop_tables()
        TestHelper.delete_data_and_temp_folder()
