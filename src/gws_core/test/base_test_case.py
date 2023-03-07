
# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from ..experiment.queue_service import QueueService
from .base_test_case_complete import BaseTestCaseComplete
from .gtest import GTest


class BaseTestCase(BaseTestCaseComplete):
    """Base class for test, contain method to ease testing and automatically init env and clear it after
    Extend this class if your tests require database. If you are only using the TaskRunner, you can use BaseTestCaseComplete.
    This will init the database which is way slower.
    If you do not need the database, use BaseTestCaseComplete
    """

    @classmethod
    def init_before_test(cls):
        GTest.delete_data_and_temp_folder()
        GTest.drop_tables()
        GTest.init_complete()

    @classmethod
    def clear_after_test(cls):
        QueueService.deinit()
        GTest.drop_tables()
        GTest.delete_data_and_temp_folder()
