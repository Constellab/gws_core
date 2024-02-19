# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import Callable


class TransactionSignleton():
    count_transaction: int = 0

    @staticmethod
    def increment() -> None:
        TransactionSignleton.count_transaction += 1

    @staticmethod
    def decrement() -> None:
        TransactionSignleton.count_transaction -= 1

        if TransactionSignleton.count_transaction < 0:
            TransactionSignleton.count_transaction = 0

    @staticmethod
    def has_transaction() -> bool:
        return TransactionSignleton.count_transaction > 0


def transaction(nested_transaction: bool = False) -> Callable:
    """Decorator to place around a method to create a new transaction
    If the method raised an exception, the transaction is rollback

    If decorated with transaction is extended the transaction is still created. If the child
    method is decorated with transaction, it will create 2 transactions

    :param nested_transaction: [description] if False only 1 transaction is created at the time and it wait the transaction
    to finish before creating a new
     If True, a transaction is created each time a method with the decorator is called (included )
    :type unique_transaction: bool
    """
    def decorator(func) -> Callable:
        def wrapper_function(*args, **kwargs):
            from ..model.model import Model

            # If we are in unique transaction mode and a transaction already exists,
            # don't create a transaction
            if not nested_transaction and TransactionSignleton.has_transaction():
                return func(*args, **kwargs)

            TransactionSignleton.increment()
            try:
                with Model.get_db_manager().db.transaction() as nested_txn:
                    try:
                        result = func(*args, **kwargs)
                    except Exception as err:
                        nested_txn.rollback()
                        raise err
                    nested_txn.commit()
            finally:
                TransactionSignleton.decrement()

            return result
        return wrapper_function
    return decorator
