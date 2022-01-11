

from typing import Any, Callable, List, Literal, Optional, Type

from gws_core.core.classes.enum_field import EnumField
from gws_core.core.exception.exceptions.bad_request_exception import \
    BadRequestException
from peewee import (Expression, Field, FloatField, IntegerField, ModelSelect,
                    Ordering)
from playhouse.mysql_ext import Match
from pydantic import BaseModel
from typing_extensions import TypedDict

from ..model.model import Model
from .expression_builder import ExpressionBuilder

SearchOperatorStr = Literal["EQ", "NEQ",  "LT", "LE", "GT", "GE", "CONTAINS", "IN", "NOT_IN", "NULL", "NOT_NULL",
                            "START_WITH", "END_WITH", "MATCH", "BETWEEN"]

SearchOrderStr = Literal["ASC", "DESC"]
SearchOrderNullOption = Literal["LAST", "FIRST"]


class SearchFilterCriteria(TypedDict):
    key: str
    operator: SearchOperatorStr
    value: Any


class SearchSortCriteria(TypedDict):
    key: str
    order: SearchOrderStr
    nullOption: Optional[SearchOrderNullOption]


class SearchDict(BaseModel):
    """Dictionnary containing information to filter and order a search

    :param TypedDict: [description]
    :type TypedDict: [type]
    """
    filtersCriteria: List[SearchFilterCriteria] = []
    sortsCriteria: Optional[List[SearchSortCriteria]] = []

    def add_filter_criteria(self, key: str, operator: SearchOperatorStr, value: Any) -> None:
        self.filtersCriteria.append({'key': key, 'operator': operator, 'value': value})

    def remove_filter_criteria(self, key: str) -> None:
        self.filtersCriteria = list(filter(lambda x: x["key"] != key, self.filtersCriteria))

    def override_filter_criteria(self, key: str, operator: SearchOperatorStr, value: Any) -> None:
        self.remove_filter_criteria(key)
        self.filtersCriteria.append({'key': key, 'operator': operator, 'value': value})


class SearchBuilder:
    """Builder to make dynamic search query with And operator

    :raises BadRequestException: [description]
    :raises BadRequestException: [description]
    :return: [description]
    :rtype: [type]
    """

    _model_type: Type[Model]
    _default_orders: List[Ordering]

    def __init__(self, model_type: Type[Model], default_order: List[Ordering] = None) -> None:
        """Create a search build to make dynamic search


        :param model_type: peewee type of the model to search
        :type model_type: Type[Model]
        :param default_order: define a default sort for the request, defaults to None
        :type default_order: List[Ordering], optional
        """
        self._model_type = model_type

        if default_order is None:
            default_orders = []
        self._default_orders = default_order

    def build_search(self, search: SearchDict) -> ModelSelect:
        filter_expression = self.build_search_filter_query(search.filtersCriteria)

        orders: List[Ordering] = self.build_search_ordering(search.sortsCriteria)

        model_select = self._model_type.select()

        if filter_expression is not None:
            model_select = model_select.where(filter_expression)

        if len(orders) > 0:
            model_select = model_select.order_by(*orders)

        return model_select

    def build_search_filter_query(self, filters: List[SearchFilterCriteria]) -> Expression:
        query_builder: ExpressionBuilder = ExpressionBuilder()

        for filter_ in filters:
            query_builder.add_expression(self.get_filter_expression(filter_))

        return query_builder.build()

    def get_filter_expression(self, filter_: SearchFilterCriteria) -> Expression:
        field: Field = self.get_model_field(filter_["key"])

        # convert the value in the correct format
        value = self.convert_value(field, filter_["value"])

        return self.get_expression(filter_["operator"], field, value)

    def build_search_ordering(self, orders: List[SearchSortCriteria]) -> List[Ordering]:
        if not orders:
            return self._default_orders

        ordering: List[Ordering] = []

        for order in orders:
            ordering.append(self.get_field_order(order))

        return ordering

    def get_field_order(self, order: SearchSortCriteria) -> Ordering:
        field: Field = self.get_model_field(order["key"])

        null_option: str = order.get('nullOption', 'LAST')

        if order["order"] == "DESC":
            return field.desc(nulls=null_option)
        else:
            return field.asc(nulls=null_option)

    def get_model_field(self, key: str) -> Field:
        """Retrieve the peewee field of the model base on field name
        """
        if not hasattr(self._model_type, key):
            raise BadRequestException(f"The model does not have a attribute named '{key}'")

        field: Field = getattr(self._model_type, key)

        if not isinstance(field, Field):
            raise BadRequestException(f"The attribte named '{key}' is not a field")

        return field

    def convert_value(self, field: Field, value: Any) -> Any:
        """Method to convert the search value (or values) to type of field
        """
        converter: Callable = self._get_converter(field)

        # if there is no converter, return the value without touching it
        if converter is None:
            return value
        if isinstance(value, list):
            values = []
            for val in value:
                values.append(converter(val))
            return values
        else:
            return converter(value)

    def _get_converter(self, field: Field) -> Callable:
        """Method that return a convert method to convert the search value to type of field
        """
        # Convert the string to enum
        if isinstance(field, EnumField):
            return field.python_value
        elif isinstance(field, IntegerField):
            return int
        elif isinstance(field, FloatField):
            return float
        else:
            return None

    def get_expression(self, operator: SearchOperatorStr, field: Field, value: Any) -> Expression:
        if operator == 'EQ':
            return field == value
        elif operator == 'NEQ':
            return field != value
        elif operator == 'LT':
            return field < value
        elif operator == 'LE':
            return field <= value
        elif operator == 'GT':
            return field > value
        elif operator == 'GE':
            return field >= value
        elif operator == 'CONTAINS':
            return field.contains(value)
        elif operator == 'START_WITH':
            return field.startswith(value)
        elif operator == 'END_WITH':
            return field.endswith(value)
        elif operator == 'IN':
            return field.in_(value)
        elif operator == 'NOT_IN':
            return field.not_in(value)
        elif operator == 'NULL':
            return field.is_null(True)
        elif operator == 'NOT_NULL':
            return field.is_null(False)
        elif operator == 'MATCH':
            return Match((field), value, modifier='IN BOOLEAN MODE')
        elif operator == 'BETWEEN':
            return field.between(value[0], value[1])
