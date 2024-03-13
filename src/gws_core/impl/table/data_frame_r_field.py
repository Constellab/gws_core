

from pandas import read_pickle
from pandas.core.frame import DataFrame

from ...impl.file.file_r_field import FileRField


class DataFrameRField(FileRField):
    """Specific RField for Dataframe, these are loaded and dumped into a file

    WARNING, this uses the pick function, only load file that you trust, otherwise it could
    execute malicious code

    :param FileRField: [description]
    :type FileRField: [type]
    """

    def __init__(self) -> None:
        super().__init__(default_value=DataFrame)

    def load_from_file(self, file_path: str) -> DataFrame:
        return read_pickle(file_path)

    def dump_to_file(self, r_field_value: DataFrame, file_path: str) -> None:
        r_field_value.to_pickle(file_path)
