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
        name = TypedCharField(max_length=255)        # -> str
        description = NullableTextField()            # -> str | None
        count = TypedIntegerField(default=0)         # -> int
        status = TypedEnumField(choices=MyStatus)    # -> MyStatus
        parent = NullableForeignKeyField(MyParent)   # -> MyParent | None

Use the ``Typed*`` variants for non-nullable columns and the ``Nullable*``
variants for nullable ones. Each variant sets ``null`` itself, so you do not
pass ``null=`` — any value you pass is overridden by the class.
"""

from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import TYPE_CHECKING, Any, Generic, Literal, TypeVar, overload

from peewee import (
    BigIntegerField,
    BooleanField,
    CharField,
    DateField,
    DecimalField,
    DeferredForeignKey,
    FloatField,
    ForeignKeyField,
    IntegerField,
    TextField,
)
from peewee import Model as PeeweeModel

from gws_core.core.classes.enum_field import EnumField
from gws_core.core.model.db_field import (
    BaseDTOField,
    DateTimeUTC,
    JSONField,
    SerializableDBField,
    SerializableObject,
)
from gws_core.core.model.model_dto import BaseModelDTO

if TYPE_CHECKING:
    from typing_extensions import Self

T = TypeVar("T")
EnumT = TypeVar("EnumT", bound=Enum)
ModelT = TypeVar("ModelT", bound=PeeweeModel)
DTOT = TypeVar("DTOT", bound=BaseModelDTO)
SerializableT = TypeVar("SerializableT", bound=SerializableObject)


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
    """``CharField`` (``null=False``) whose instance value is typed ``str``."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        kwargs["null"] = False
        super().__init__(*args, **kwargs)


class NullableCharField(TypedDbField[str | None], CharField):
    """``CharField`` (``null=True``) whose instance value is typed ``str | None``."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        kwargs["null"] = True
        super().__init__(*args, **kwargs)


class TypedTextField(TypedDbField[str], TextField):
    """``TextField`` (``null=False``) whose instance value is typed ``str``."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        kwargs["null"] = False
        super().__init__(*args, **kwargs)


class NullableTextField(TypedDbField[str | None], TextField):
    """``TextField`` (``null=True``) whose instance value is typed ``str | None``."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        kwargs["null"] = True
        super().__init__(*args, **kwargs)


class TypedBooleanField(TypedDbField[bool], BooleanField):
    """``BooleanField`` (``null=False``) whose instance value is typed ``bool``."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        kwargs["null"] = False
        super().__init__(*args, **kwargs)


class NullableBooleanField(TypedDbField[bool | None], BooleanField):
    """``BooleanField`` (``null=True``) whose instance value is typed ``bool | None``."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        kwargs["null"] = True
        super().__init__(*args, **kwargs)


class TypedIntegerField(TypedDbField[int], IntegerField):
    """``IntegerField`` (``null=False``) whose instance value is typed ``int``."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        kwargs["null"] = False
        super().__init__(*args, **kwargs)


class NullableIntegerField(TypedDbField[int | None], IntegerField):
    """``IntegerField`` (``null=True``) whose instance value is typed ``int | None``."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        kwargs["null"] = True
        super().__init__(*args, **kwargs)


class TypedBigIntegerField(TypedDbField[int], BigIntegerField):
    """``BigIntegerField`` (``null=False``) whose instance value is typed ``int``."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        kwargs["null"] = False
        super().__init__(*args, **kwargs)


class NullableBigIntegerField(TypedDbField[int | None], BigIntegerField):
    """``BigIntegerField`` (``null=True``) whose instance value is typed ``int | None``."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        kwargs["null"] = True
        super().__init__(*args, **kwargs)


class TypedFloatField(TypedDbField[float], FloatField):
    """``FloatField`` (``null=False``) whose instance value is typed ``float``."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        kwargs["null"] = False
        super().__init__(*args, **kwargs)


class NullableFloatField(TypedDbField[float | None], FloatField):
    """``FloatField`` (``null=True``) whose instance value is typed ``float | None``."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        kwargs["null"] = True
        super().__init__(*args, **kwargs)


class TypedDateField(TypedDbField[date], DateField):
    """``DateField`` (``null=False``) whose instance value is typed ``date``."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        kwargs["null"] = False
        super().__init__(*args, **kwargs)


class NullableDateField(TypedDbField[date | None], DateField):
    """``DateField`` (``null=True``) whose instance value is typed ``date | None``."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        kwargs["null"] = True
        super().__init__(*args, **kwargs)


class TypedDecimalField(TypedDbField[Decimal], DecimalField):
    """``DecimalField`` (``null=False``) whose instance value is typed ``Decimal``."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        kwargs["null"] = False
        super().__init__(*args, **kwargs)


class NullableDecimalField(TypedDbField[Decimal | None], DecimalField):
    """``DecimalField`` (``null=True``) whose instance value is typed ``Decimal | None``."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        kwargs["null"] = True
        super().__init__(*args, **kwargs)


class TypedDateTimeUTC(TypedDbField[datetime], DateTimeUTC):
    """``DateTimeUTC`` (``null=False``) whose instance value is typed ``datetime``."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        kwargs["null"] = False
        super().__init__(*args, **kwargs)


class NullableDateTimeUTC(TypedDbField[datetime | None], DateTimeUTC):
    """``DateTimeUTC`` (``null=True``) whose instance value is typed ``datetime | None``."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        kwargs["null"] = True
        super().__init__(*args, **kwargs)


class TypedJSONField(TypedDbField[Any], JSONField):
    """``JSONField`` (``null=False``) whose instance value is typed ``Any`` (decoded JSON)."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        kwargs["null"] = False
        super().__init__(*args, **kwargs)


class NullableJSONField(TypedDbField[Any | None], JSONField):
    """``JSONField`` (``null=True``) whose instance value is typed ``Any | None``."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        kwargs["null"] = True
        super().__init__(*args, **kwargs)


class TypedEnumField(TypedDbField[EnumT], EnumField):
    """
    ``EnumField`` (``null=False``) whose instance value is typed with the enum passed as ``choices``.

    The enum type is inferred from the constructor, no annotation needed:

        status = TypedEnumField(choices=MyStatus)   # instance value typed MyStatus
    """

    def __init__(
        self, *args: Any, choices: type[EnumT], max_length: int = 255, **kwargs: Any
    ) -> None:
        kwargs["null"] = False
        super().__init__(*args, choices=choices, max_length=max_length, **kwargs)


class NullableEnumField(TypedDbField[EnumT | None], EnumField):
    """
    ``EnumField`` (``null=True``) whose instance value is typed ``Enum | None``.

    The enum type is inferred from the constructor, no annotation needed:

        status = NullableEnumField(choices=MyStatus)   # -> MyStatus | None
    """

    def __init__(
        self, *args: Any, choices: type[EnumT], max_length: int = 255, **kwargs: Any
    ) -> None:
        kwargs["null"] = True
        super().__init__(*args, choices=choices, max_length=max_length, **kwargs)


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

    def __init__(self, model: Any, *args: Any, **kwargs: Any) -> None:
        kwargs["null"] = False
        super().__init__(model, *args, **kwargs)


class NullableForeignKeyField(TypedDbField[ModelT | None], ForeignKeyField):
    """
    ``ForeignKeyField`` (``null=True``) whose instance value is typed ``Model | None``.

    The related model type is inferred from the constructor, no annotation needed:

        owner = NullableForeignKeyField(User)   # -> User | None

    For a self-reference, the model type cannot be inferred from the ``"self"``
    string: specialize the generic explicitly (as a forward reference, since the
    class is not defined yet inside its own body):

        parent = NullableForeignKeyField["MyModel"]("self")   # -> MyModel | None
    """

    if TYPE_CHECKING:

        @overload
        def __init__(self, model: type[ModelT], *args: Any, **kwargs: Any) -> None: ...

        @overload
        def __init__(self, model: Literal["self"], *args: Any, **kwargs: Any) -> None: ...

    def __init__(self, model: Any, *args: Any, **kwargs: Any) -> None:
        kwargs["null"] = True
        super().__init__(model, *args, **kwargs)


class TypedForeignKeyIdField(TypedDbField[str], ForeignKeyField):
    """
    ``ForeignKeyField`` (``null=False``, ``lazy_load=False``) whose instance value is the
    related row's id, typed ``str``.

    With ``lazy_load=False`` peewee never loads the related row: instance access
    returns the raw foreign-key id (a ``str``) instead of the related model. Use
    this when you only ever need the id and want to avoid the extra query:

        scenario = TypedForeignKeyIdField(Scenario)   # -> str (the scenario id)

    For a self-reference, pass ``"self"`` (no generic to specialize, the value is
    always a ``str``):

        parent = TypedForeignKeyIdField("self")   # -> str
    """

    if TYPE_CHECKING:

        @overload
        def __init__(self, model: type[PeeweeModel], *args: Any, **kwargs: Any) -> None: ...

        @overload
        def __init__(self, model: Literal["self"], *args: Any, **kwargs: Any) -> None: ...

    def __init__(self, model: Any, *args: Any, **kwargs: Any) -> None:
        kwargs["null"] = False
        kwargs["lazy_load"] = False
        super().__init__(model, *args, **kwargs)


class NullableForeignKeyIdField(TypedDbField[str | None], ForeignKeyField):
    """
    ``ForeignKeyField`` (``null=True``, ``lazy_load=False``) whose instance value is the
    related row's id, typed ``str | None``.

    With ``lazy_load=False`` peewee never loads the related row: instance access
    returns the raw foreign-key id (a ``str``, or ``None`` when unset) instead of
    the related model. Use this when you only ever need the id and want to avoid
    the extra query:

        source = NullableForeignKeyIdField(ResourceModel)   # -> str | None

    For a self-reference, pass ``"self"`` (no generic to specialize, the value is
    always ``str | None``):

        parent = NullableForeignKeyIdField("self")   # -> str | None
    """

    if TYPE_CHECKING:

        @overload
        def __init__(self, model: type[PeeweeModel], *args: Any, **kwargs: Any) -> None: ...

        @overload
        def __init__(self, model: Literal["self"], *args: Any, **kwargs: Any) -> None: ...

    def __init__(self, model: Any, *args: Any, **kwargs: Any) -> None:
        kwargs["null"] = True
        kwargs["lazy_load"] = False
        super().__init__(model, *args, **kwargs)


class TypedDeferredForeignKeyIdField(TypedDbField[str], DeferredForeignKey):
    """
    ``DeferredForeignKey`` (``null=False``, ``lazy_load=False``) whose instance value is the
    related row's id, typed ``str``.

    Like :class:`TypedForeignKeyIdField` but for a deferred FK (related model
    referenced by string name, resolved once all tables exist). The value is
    always the raw id, so there is no generic to specialize:

        ref = TypedDeferredForeignKeyIdField("OtherModel")   # -> str
    """

    def __init__(self, rel_model_name: str, *args: Any, **kwargs: Any) -> None:
        kwargs["null"] = False
        kwargs["lazy_load"] = False
        super().__init__(rel_model_name, *args, **kwargs)


class NullableDeferredForeignKeyIdField(TypedDbField[str | None], DeferredForeignKey):
    """
    ``DeferredForeignKey`` (``null=True``, ``lazy_load=False``) whose instance value is the
    related row's id, typed ``str | None``.

    Like :class:`NullableForeignKeyIdField` but for a deferred FK (related model
    referenced by string name, resolved once all tables exist). The value is
    always the raw id, so there is no generic to specialize:

        ref = NullableDeferredForeignKeyIdField("OtherModel")   # -> str | None
    """

    def __init__(self, rel_model_name: str, *args: Any, **kwargs: Any) -> None:
        kwargs["null"] = True
        kwargs["lazy_load"] = False
        super().__init__(rel_model_name, *args, **kwargs)


class TypedDeferredForeignKeyField(TypedDbField[ModelT], DeferredForeignKey):
    """
    ``DeferredForeignKey`` (``null=False``) whose instance value is typed with the related model.

    The related model is referenced by string name (the FK is resolved later,
    once all tables exist), so its type cannot be inferred from the argument:
    specialize the generic explicitly. The related class is usually not
    importable here — that is the reason the FK is deferred — so import it under
    ``TYPE_CHECKING`` and use it as a forward reference:

        if TYPE_CHECKING:
            from ...other_model import OtherModel

        ref = TypedDeferredForeignKeyField["OtherModel"]("OtherModel")   # -> OtherModel
    """

    def __init__(self, rel_model_name: str, *args: Any, **kwargs: Any) -> None:
        kwargs["null"] = False
        super().__init__(rel_model_name, *args, **kwargs)


class NullableDeferredForeignKeyField(TypedDbField[ModelT | None], DeferredForeignKey):
    """
    ``DeferredForeignKey`` (``null=True``) whose instance value is typed ``Model | None``.

    The related model is referenced by string name (the FK is resolved later,
    once all tables exist), so its type cannot be inferred from the argument:
    specialize the generic explicitly. The related class is usually not
    importable here — that is the reason the FK is deferred — so import it under
    ``TYPE_CHECKING`` and use it as a forward reference:

        if TYPE_CHECKING:
            from ...other_model import OtherModel

        ref = NullableDeferredForeignKeyField["OtherModel"](
            "OtherModel", backref="+", lazy_load=False
        )                                                        # -> OtherModel | None
    """

    def __init__(self, rel_model_name: str, *args: Any, **kwargs: Any) -> None:
        kwargs["null"] = True
        super().__init__(rel_model_name, *args, **kwargs)


class TypedBaseDTOField(TypedDbField[DTOT], BaseDTOField):
    """
    ``BaseDTOField`` (``null=False``) whose instance value is typed with the DTO passed as ``dto_type``.

    The DTO type is inferred from the constructor, no annotation needed:

        config = TypedBaseDTOField(MyConfigDTO)   # instance value typed MyConfigDTO
    """

    def __init__(self, dto_type: type[DTOT], *args: Any, **kwargs: Any) -> None:
        kwargs["null"] = False
        super().__init__(dto_type, *args, **kwargs)


class NullableBaseDTOField(TypedDbField[DTOT | None], BaseDTOField):
    """
    ``BaseDTOField`` (``null=True``) whose instance value is typed ``DTO | None``.

    The DTO type is inferred from the constructor, no annotation needed:

        config = NullableBaseDTOField(MyConfigDTO)   # -> MyConfigDTO | None
    """

    def __init__(self, dto_type: type[DTOT], *args: Any, **kwargs: Any) -> None:
        kwargs["null"] = True
        super().__init__(dto_type, *args, **kwargs)


class TypedSerializableDBField(TypedDbField[SerializableT], SerializableDBField):
    """
    ``SerializableDBField`` (``null=False``) whose instance value is typed with the object passed as ``object_type``.

    The object type is inferred from the constructor, no annotation needed:

        data = TypedSerializableDBField(MyObject)   # instance value typed MyObject
    """

    def __init__(self, object_type: type[SerializableT], *args: Any, **kwargs: Any) -> None:
        kwargs["null"] = False
        super().__init__(object_type, *args, **kwargs)


class NullableSerializableDBField(TypedDbField[SerializableT | None], SerializableDBField):
    """
    ``SerializableDBField`` (``null=True``) whose instance value is typed ``object | None``.

    The object type is inferred from the constructor, no annotation needed:

        data = NullableSerializableDBField(MyObject)   # -> MyObject | None
    """

    def __init__(self, object_type: type[SerializableT], *args: Any, **kwargs: Any) -> None:
        kwargs["null"] = True
        super().__init__(object_type, *args, **kwargs)
