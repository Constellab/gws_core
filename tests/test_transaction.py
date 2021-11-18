
from gws_core import config
from gws_core.config.config import Config
from gws_core.core.decorator.transaction import (TransactionSignleton,
                                                 transaction)
from gws_core.test.base_test_case import BaseTestCase


class TestTransaction(BaseTestCase):

    def test_transaction(self):
        # test the transaction worked
        config = Config()
        self._create_config_success(config)
        self.assertIsNotNone(Config.get_by_id(config.id))

        # test the transaction did not saved when there is an exception
        config = Config()
        try:
            self._create_config_error(config)
        except:
            pass
        self.assertIsNone(Config.get_by_id(config.id))

        # test the transaction did save even if there is an error because the nested option is one
        config = Config()
        try:
            self._create_config_error_nested(config)
        except:
            pass
        self.assertIsNotNone(Config.get_by_id(config.id))

    @transaction()
    def _create_config_success(self, config: Config) -> Config:
        return config.save()

    @transaction()
    def _create_config_error(self, config: Config) -> None:
        self._create_config_success(config)
        raise Exception()

    @transaction(nested_transaction=True)
    def _create_config_success_nested(self, config: Config) -> Config:
        return config.save()

    @transaction()
    def _create_config_error_nested(self, config: Config) -> None:
        self._create_config_success_nested(config)
        raise Exception()
