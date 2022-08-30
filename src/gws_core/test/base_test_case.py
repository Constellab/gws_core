
# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com
from typing import List, Union
from unittest.async_case import IsolatedAsyncioTestCase

from gws_core.core.utils.utils import Utils
from gws_core.progress_bar.progress_bar import ProgressBar

from ..experiment.queue_service import QueueService
from .gtest import GTest


class BaseTestCase(IsolatedAsyncioTestCase):
    """Base class for test, contain method to ease testing and automatically init env and clear it after
    """

    # default value of ignore keys when comparing json
    json_ignore_keys: List[str] = ["id", "created_at", "last_modified_at"]

    # If true the init and clear are called for each test,
    # If False they are called before and after all the class tests
    init_before_each_test: bool = False

    # use to call set up and tear down class only once
    _class_setted_up: bool = False
    _class_teared_down: bool = False

    @classmethod
    def setUpClass(cls):
        if cls._class_setted_up:
            return
        print(f"************** Running test file '{cls.__module__}', class '{cls.__name__}' **************")
        if not cls.init_before_each_test:
            cls.init_before_test()
        cls._class_setted_up = True

        # remove the delay from the progress bar to avoid problem during tests
        ProgressBar._MIN_ALLOWED_DELTA_TIME = 0

    @classmethod
    def tearDownClass(cls):
        if cls._class_teared_down:
            return
        if not cls.init_before_each_test:
            cls.clear_after_test()
        print(f"************** End of test file '{cls.__module__}', class '{cls.__name__}' **************")
        cls._class_teared_down = True

    def setUp(self) -> None:
        if self.init_before_each_test:
            self.init_before_test()

    def tearDown(self) -> None:
        if self.init_before_each_test:
            self.clear_after_test()

    @classmethod
    def init_before_test(cls):
        #print(f'Setup: {cls}')
        GTest.delete_data_and_temp_folder()
        GTest.drop_tables()
        GTest.init()

    @classmethod
    def clear_after_test(cls):
        #print(f'Tear down: {cls}')
        QueueService.deinit()
        GTest.drop_tables()
        GTest.delete_data_and_temp_folder()

    @classmethod
    def print(cls, text):
        GTest.print(text)

    @classmethod
    def assert_json(cls, json_1: Union[dict, list], json_2: Union[dict, list], ignore_keys: List[str] = None) -> None:
        """Assert a json with possibility to ignore key
        """
        Utils.assert_json_equals(json_1, json_2, ignore_keys)
