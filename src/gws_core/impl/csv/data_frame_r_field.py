from typing import Any

from pandas.core.frame import DataFrame

from ...resource.r_field import RField


class DataFrameRField(RField):

    def __init__(self) -> None:
        super().__init__(searchable=False, default_value=DataFrame())

    def load(self, object_: Any) -> DataFrame:
        return DataFrame.from_dict(data=object_)

    def dump(self, object_: DataFrame) -> Any:
        return object_.to_dict()
