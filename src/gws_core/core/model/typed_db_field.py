"""
Typed peewee fields for static type checkers.

Peewee fields are descriptors: accessed on the class they return the field
itself (to build queries like ``cls.name == 'x'``), accessed on an instance
they return the column value. Peewee implements this at runtime (via its
``FieldAccessor``) but does not declare it to type checkers, so Pylance sees
``self.name`` as a ``CharField`` instead of a ``str``.

The fields in this module fix this at the typing level only: the
``TypedDbField`` mixin declares ``__get__`` overloads (under ``TYPE_CHECKING``)
that describe what peewee already does at runtime. They have zero runtime
behavior and are drop-in replacements for their peewee counterparts.

Usage in a model:

    class MyModel(Model):
        name = TypedCharField(max_length=255, null=False)        # -> str
        description = NullableTextField(null=True)               # -> str | None
        count = TypedIntegerField(default=0)                     # -> int
        status = TypedEnumField(choices=MyStatus)                # -> MyStatus
        parent = NullableForeignKeyField(MyParent, null=True)    # -> MyParent | None

Use the ``Typed*`` variants for non-nullable columns and the ``Nullable*``
variants for nullable ones (``null=True``).
"""

from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import TYPE_CHECKING, Any, Generic, Literal, TypeVar, overload

from peewee import (
    BooleanField,
    CharField,
    DateField,
    DecimalField,
    FloatField,
    ForeignKeyField,
    IntegerField,
    TextField,
)
from peewee import Model as PeeweeModel

from gws_core.core.classes.enum_field import EnumField
from gws_core.core.model.db_field import DateTimeUTC

if TYPE_CHECKING:
    from typing_extensions import Self

T = TypeVar("T")
EnumT = TypeVar("EnumT", bound=Enum)
ModelT = TypeVar("ModelT", bound=PeeweeModel)


class TypedDbField(Generic[T]):
    """
    Typing-only mixin that declares the descriptor protocol of peewee fields.

    It tells the type checker that:
    - class access (``MyModel.my_field``) returns the field itself, so query
      building (``where``, ``order_by``, ``==``, ``in_`` ...) keeps working
    - instance access (``my_model.my_field``) returns the column value, typed ``T``
    - instance assignment (``my_model.my_field = value``) expects a value of type ``T``

    The whole body lives under ``TYPE_CHECKING``: at runtime this class is
    empty and peewee's own ``FieldAccessor`` does the real work, so combining
    this mixin with a peewee field changes no behavior.
    """

    if TYPE_CHECKING:

        @overload
        def __get__(self, instance: None, owner: Any) -> "Self": ...

        @overload
        def __get__(self, instance: object, owner: Any) -> T: ...

        def __get__(self, instance: object | None, owner: Any) -> Any: ...

        def __set__(self, instance: object, value: T) -> None: ...


class TypedCharField(TypedDbField[str], CharField):
    """``CharField`` whose instance value is typed ``str``."""


class NullableCharField(TypedDbField[str | None], CharField):
    """``CharField`` (``null=True``) whose instance value is typed ``str | None``."""


class TypedTextField(TypedDbField[str], TextField):
    """``TextField`` whose instance value is typed ``str``."""


class NullableTextField(TypedDbField[str | None], TextField):
    """``TextField`` (``null=True``) whose instance value is typed ``str | None``."""


class TypedBooleanField(TypedDbField[bool], BooleanField):
    """``BooleanField`` whose instance value is typed ``bool``."""


class NullableBooleanField(TypedDbField[bool | None], BooleanField):
    """``BooleanField`` (``null=True``) whose instance value is typed ``bool | None``."""


class TypedIntegerField(TypedDbField[int], IntegerField):
    """``IntegerField`` whose instance value is typed ``int``."""


class NullableIntegerField(TypedDbField[int | None], IntegerField):
    """``IntegerField`` (``null=True``) whose instance value is typed ``int | None``."""


class TypedFloatField(TypedDbField[float], FloatField):
    """``FloatField`` whose instance value is typed ``float``."""


class NullableFloatField(TypedDbField[float | None], FloatField):
    """``FloatField`` (``null=True``) whose instance value is typed ``float | None``."""


class TypedDateField(TypedDbField[date], DateField):
    """``DateField`` whose instance value is typed ``date``."""


class NullableDateField(TypedDbField[date | None], DateField):
    """``DateField`` (``null=True``) whose instance value is typed ``date | None``."""


class TypedDecimalField(TypedDbField[Decimal], DecimalField):
    """``DecimalField`` whose instance value is typed ``Decimal``."""


class NullableDecimalField(TypedDbField[Decimal | None], DecimalField):
    """``DecimalField`` (``null=True``) whose instance value is typed ``Decimal | None``."""


class TypedDateTimeUTC(TypedDbField[datetime], DateTimeUTC):
    """``DateTimeUTC`` whose instance value is typed ``datetime``."""


class NullableDateTimeUTC(TypedDbField[datetime | None], DateTimeUTC):
    """``DateTimeUTC`` (``null=True``) whose instance value is typed ``datetime | None``."""


class TypedEnumField(TypedDbField[EnumT], EnumField):
    """
    ``EnumField`` whose instance value is typed with the enum passed as ``choices``.

    The enum type is inferred from the constructor, no annotation needed:

        status = TypedEnumField(choices=MyStatus)   # instance value typed MyStatus
    """

    if TYPE_CHECKING:

        def __init__(
            self, *args: Any, choices: type[EnumT], max_length: int = 255, **kwargs: Any
        ) -> None: ...


class NullableEnumField(TypedDbField[EnumT | None], EnumField):
    """
    ``EnumField`` (``null=True``) whose instance value is typed ``Enum | None``.

    The enum type is inferred from the constructor, no annotation needed:

        status = NullableEnumField(choices=MyStatus, null=True)   # -> MyStatus | None
    """

    if TYPE_CHECKING:

        def __init__(
            self, *args: Any, choices: type[EnumT], max_length: int = 255, **kwargs: Any
        ) -> None: ...


class TypedForeignKeyField(TypedDbField[ModelT], ForeignKeyField):
    """
    ``ForeignKeyField`` whose instance value is typed with the related model.

    The related model type is inferred from the constructor, no annotation needed:

        owner = TypedForeignKeyField(User)   # instance value typed User

    For a self-reference, the model type cannot be inferred from the ``"self"``
    string: specialize the generic explicitly (as a forward reference, since the
    class is not defined yet inside its own body):

        parent = TypedForeignKeyField["MyModel"]("self")   # -> MyModel
    """

    if TYPE_CHECKING:

        @overload
        def __init__(self, model: type[ModelT], *args: Any, **kwargs: Any) -> None: ...

        @overload
        def __init__(self, model: Literal["self"], *args: Any, **kwargs: Any) -> None: ...

        def __init__(self, model: Any, *args: Any, **kwargs: Any) -> None: ...


class NullableForeignKeyField(TypedDbField[ModelT | None], ForeignKeyField):
    """
    ``ForeignKeyField`` (``null=True``) whose instance value is typed ``Model | None``.

    The related model type is inferred from the constructor, no annotation needed:

        owner = NullableForeignKeyField(User, null=True)   # -> User | None

    For a self-reference, the model type cannot be inferred from the ``"self"``
    string: specialize the generic explicitly (as a forward reference, since the
    class is not defined yet inside its own body):

        parent = NullableForeignKeyField["MyModel"]("self", null=True)   # -> MyModel | None
    """

    if TYPE_CHECKING:

        @overload
        def __init__(self, model: type[ModelT], *args: Any, **kwargs: Any) -> None: ...

        @overload
        def __init__(self, model: Literal["self"], *args: Any, **kwargs: Any) -> None: ...

        def __init__(self, model: Any, *args: Any, **kwargs: Any) -> None: ...
