from gws_core.scenario.queue.queue_runner import QueueRunner

from .base_test_case_light import BaseTestCaseLight
from .test_helper import TestHelper


class BaseTestCase(BaseTestCaseLight):
    """Base class for test, contain method to ease testing and automatically init env and clear it after
    Extend this class if your tests require database. If you are only using the TaskRunner, you can use BaseTestCaseComplete.
    This will init the database which is way slower.
    If you do not need the database, use BaseTestCaseLight
    """

    # True once the heavy DB init has run at least once in this process.
    # After that we TRUNCATE between classes instead of dropping + recreating tables.
    _db_ever_initialized: bool = False

    @classmethod
    def init_before_test(cls):
        TestHelper.delete_data_and_temp_folder()
        if BaseTestCase._db_ever_initialized:
            # Schema already exists; just wipe data. Avoids DDL round-trips.
            TestHelper.truncate_tables()
        else:
            TestHelper.drop_tables()
        TestHelper.init_complete()
        BaseTestCase._db_ever_initialized = True

    @classmethod
    def clear_after_test(cls):
        # Intentionally skip drop_tables here: the next heavy class's setUp
        # will TRUNCATE before running, so a symmetric teardown is wasted DDL.
        QueueRunner.deinit()
        TestHelper.delete_data_and_temp_folder()
