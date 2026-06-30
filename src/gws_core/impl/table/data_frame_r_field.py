from typing import cast

from pandas import read_parquet, read_pickle
from pandas.core.frame import DataFrame

from ...impl.file.file_r_field import FileRField

# Magic bytes at the start (and end) of every Apache Parquet file. Used to tell a
# parquet-encoded DataFrame from a legacy pickle one, since KVStore files are stored
# without an extension (see KVStore.set_file) so the format cannot be read off the name.
_PARQUET_MAGIC = b"PAR1"


class DataFrameRField(FileRField[DataFrame]):
    """Specific RField for Dataframe, these are loaded and dumped into a file.

    DataFrames are dumped to Parquet (columnar, compressed, no code-execution risk on
    read). For backward compatibility, ``load_from_file`` still reads legacy pickle files:
    it sniffs the parquet magic bytes and falls back to ``read_pickle`` when they are
    absent, so DataFrames saved before this change keep loading.

    A DataFrame that Parquet cannot represent (e.g. object columns holding arbitrary
    Python objects) falls back to pickle on dump, so a save never fails.

    WARNING: pickle files (legacy files, and the rare fallback above) are read with
    pandas' pickle reader, which can execute arbitrary code. Only load files that you
    trust. DataFrames written as Parquet are not affected by this risk.

    :param FileRField: [description]
    :type FileRField: [type]
    """

    def __init__(self) -> None:
        super().__init__(default_value=DataFrame)

    def load_from_file(self, file_path: str) -> DataFrame:
        if self._is_parquet_file(file_path):
            return cast(DataFrame, read_parquet(file_path))
        # Legacy DataFrames were stored with pickle; keep reading them.
        return cast(DataFrame, read_pickle(file_path))

    def dump_to_file(self, r_field_value: DataFrame, file_path: str) -> None:
        try:
            r_field_value.to_parquet(file_path)
        except Exception:
            # Parquet cannot represent every DataFrame (e.g. object columns holding
            # arbitrary Python objects). Fall back to pickle so the save never fails;
            # load_from_file sniffs the format and reads it back correctly.
            r_field_value.to_pickle(file_path)

    @staticmethod
    def _is_parquet_file(file_path: str) -> bool:
        """Return True if the file starts with the Parquet magic bytes."""
        with open(file_path, "rb") as file:
            return file.read(len(_PARQUET_MAGIC)) == _PARQUET_MAGIC
