from __future__ import annotations

from typing import TYPE_CHECKING, Callable, List, Type

if TYPE_CHECKING:
    from ..model.model import Model


def JsonIgnore(ignore_fields: List[str]) -> Callable:
    """Class decorator to define a list of field that will be ignore during the to_json method
    This is manage by the model class. It must be a model and the to_json call the super to_json()

    :param ignore_fields: [description]
    :type ignore_fields: List[str]
    :return: [description]
    :rtype: Callable
    """

    def decorator(any_class: Type[Model]) -> Type:
        # pylint: disable=protected-access
        # save the fields to ignore in _json_ignore_fields class proprty
        if any_class._json_ignore_fields is None:
            any_class._json_ignore_fields = ignore_fields
        else:
            # for child classes, append the ignore field from parent fields
            any_class._json_ignore_fields = ignore_fields + any_class._json_ignore_fields
        return any_class

    return decorator
