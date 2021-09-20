

from typing import Any, Callable, Dict, List

from gws_core.core.classes.validator import (BoolValidator, DictValidator,
                                             FloatValidator, IntValidator,
                                             ListValidator, StrValidator,
                                             Validator)


class RField():

    searchable: bool
    _loader: Callable
    _dumper: Callable
    default_value: Any

    def __init__(self, searchable: bool = False, loader: Callable[[Any], Any] = None,
                 dumper: Callable[[Any], Any] = None, default_value: Any = None) -> None:
        self.searchable = searchable
        self._loader = loader
        self._dumper = dumper
        self.default_value = default_value

    def load(self, object_: Any) -> Any:
        if object_ is None:
            return self.default_value

        if self._loader is None:
            return object_

        return self._loader(object_)

    def dump(self, object_: Any) -> Any:
        if object_ is None:
            return self.default_value

        if self._dumper is None:
            return object_

        return self._dumper(object_)


class PrimitiveRField(RField):

    validator: Validator

    def __init__(self, validator: Validator,
                 searchable: bool = False,
                 loader: Callable[[Any], Any] = None,
                 dumper: Callable[[Any], Any] = None,
                 default_value: Any = None
                 ) -> None:
        super().__init__(searchable=searchable, loader=loader, dumper=dumper, default_value=default_value)
        self.validator = validator

    def load(self, object_: Any) -> Any:
        validated_value = self.validator.validate(object_)
        return super().load(validated_value)

    def dump(self, object_: Any) -> Any:
        validated_value = super().dump(object_)

        return self.validator.validate(validated_value)


class IntRField(PrimitiveRField):

    def __init__(self, loader: Callable[[int], Any] = None,
                 dumper: Callable[[Any], int] = None,
                 default_value: int = None) -> None:
        super().__init__(validator=IntValidator(), searchable=True, loader=loader, dumper=dumper, default_value=default_value)


class FloatRField(PrimitiveRField):

    def __init__(self, loader: Callable[[float], Any] = None,
                 dumper: Callable[[Any], float] = None,
                 default_value: float = None) -> None:
        super().__init__(validator=FloatValidator(), searchable=True, loader=loader, dumper=dumper, default_value=default_value)


class BoolRField(PrimitiveRField):

    def __init__(self, loader: Callable[[float], Any] = None,
                 dumper: Callable[[Any], float] = None,
                 default_value: bool = None) -> None:
        super().__init__(validator=BoolValidator(), searchable=True, loader=loader, dumper=dumper, default_value=default_value)


class StrRField(PrimitiveRField):

    def __init__(self, searchable: bool = False,
                 loader: Callable[[str], Any] = None,
                 dumper: Callable[[Any], str] = None,
                 default_value: str = None) -> None:
        super().__init__(validator=StrValidator(), searchable=searchable, loader=loader, dumper=dumper, default_value=default_value)


class ListRField(PrimitiveRField):

    def __init__(self, loader: Callable[[str], Any] = None,
                 dumper: Callable[[Any], str] = None,
                 default_value: List = None) -> None:
        if default_value is None:
            default_value = []
        super().__init__(validator=ListValidator(), searchable=False, loader=loader, dumper=dumper,
                         default_value=default_value)


class DictRField(PrimitiveRField):

    def __init__(self, loader: Callable[[str], Any] = None,
                 dumper: Callable[[Any], str] = None,  default_value: Dict = None) -> None:
        if default_value is None:
            default_value = {}
        super().__init__(validator=DictValidator(), searchable=False, loader=loader, dumper=dumper,
                         default_value=default_value)
