
# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import List, Union
from unittest.async_case import IsolatedAsyncioTestCase

from ...experiment.queue_service import QueueService
from .gtest import GTest


class BaseTestCase(IsolatedAsyncioTestCase):
    """Base class for test, contain method to ease testing and automatically init env and clear it after
    """

    # default value of ignore keys when comparing json
    json_ignore_keys: List[str] = ["uri", "save_datetime", "creation_datetime"]

    # If true the init and clear are called for each test,
    # If False they are called before and after all the class tests
    init_before_each_test: bool = False

    @classmethod
    def setUpClass(cls):
        if not cls.init_before_each_test:
            cls.init_before_test()

    @classmethod
    def tearDownClass(cls):
        if not cls.init_before_each_test:
            cls.clear_after_test()

    def setUp(self) -> None:
        if self.init_before_each_test:
            self.init_before_test()

    def tearDown(self) -> None:
        if self.init_before_each_test:
            self.clear_after_test()

    @classmethod
    def init_before_test(cls):
        print(f'Setup : {cls}')
        GTest.delete_data_and_temp_folder()
        GTest.drop_tables()
        GTest.create_tables()
        GTest.init()

    @classmethod
    def clear_after_test(cls):
        print(f'Tear down : {cls}')
        GTest.delete_data_and_temp_folder()
        QueueService.deinit()
        GTest.drop_tables()

    @classmethod
    def print(cls, text):
        GTest.print(text)

    def assert_json(self, json_1: Union[dict, list], json_2: Union[dict, list], ignore_keys: List[str] = None) -> None:
        """Assert a json with possibility to ignore key
        """
        self._assert_json_recur(json_1, json_2, ignore_keys, "")

    def _assert_json_recur(
            self, json_1: Union[dict, list],
            json_2: Union[dict, list],
            ignore_keys: List[str] = None,
            cumulated_key: str = "") -> bool:

        # handle list
        if isinstance(json_1, list):
            if not isinstance(json_2, list):
                raise AssertionError(
                    f"The seconde object is not a list for key '{cumulated_key}'.")

            if len(json_1) != len(json_2):
                raise AssertionError(
                    f"Length of array different for key '{cumulated_key}'.")

            for index, value in enumerate(json_1):
                self._assert_json_recur(value, json_2[index], ignore_keys, f"{cumulated_key}[{index}]")

            return None

        # Handle dict
        if isinstance(json_1, dict):
            if not isinstance(json_1, dict):
                raise AssertionError(
                    f"The seconde object is not a dict for key '{cumulated_key}'.")

            if len(json_1) != len(json_2):
                raise AssertionError(
                    f"Length of object different for key '{cumulated_key}'.")

            for key, value in json_1.items():
                if ignore_keys and key in ignore_keys:
                    continue

                self._assert_json_recur(value, json_2[key], ignore_keys, f"{cumulated_key}.{key}")

            return None

        # Handle primitive value
        if json_1 != json_2:
            raise AssertionError(
                f"Values differents for key '{cumulated_key}'. First : '{json_1}'. Seconde : '{json_2}'")
