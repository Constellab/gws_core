# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import Type

from gws_core.impl.file.file import File

from ....config.config_types import ConfigParams, ConfigSpecs
from ....config.param_spec import StrParam
from ....core.exception.exceptions import BadRequestException
from ....task.converter.exporter import exporter_decorator
from ....task.converter.importer import importer_decorator
from ..table import Table
from ..tasks.table_exporter import TableExporter
from ..tasks.table_importer import TableImporter
from .metadata_table import MetadataTable

# ####################################################################
#
# Importer class
#
# ####################################################################


@importer_decorator("MetadataTableImporter", target_type=MetadataTable, supported_extensions=Table.ALLOWED_FILE_FORMATS)
class MetadataTableImporter(TableImporter):

    config_specs: ConfigSpecs = {
        'delimiter':
        StrParam(
            allowed_values=Table.ALLOWED_DELIMITER, default_value=Table.DEFAULT_DELIMITER,
            human_name="Delimiter",
            short_description="Delimiter character. Only for parsing CSV files")
    }

    async def import_from_path(self, file: File, params: ConfigParams, target_type: Type[MetadataTable]) -> MetadataTable:
        """
        Import from a repository

        :param file: The file to import
        :type file: `File`
        :param params: The config params
        :type params: `ConfigParams`
        :returns: the parsed metadata
        :rtype: MetadataTable
        """

        params["index_column"] = None
        params["comment"] = "#"
        csv_table: MetadataTable = await super().import_from_path(file, params, target_type)

        sample_id_column = csv_table.column_names[0]
        if not sample_id_column:
            raise BadRequestException(
                f"Cannot import MetadataTable. A name is required for the sample_id column (i.e. the first column)")

        # sample_id_column = params.get_value("sample_id_column", MetadataTable.DEFAULT_SAMPLE_ID_COLUMN)
        # if not csv_table.column_exists(sample_id_column):
        #     raise BadRequestException(
        #         f"Cannot import MetadataTable. No sample-id column found (no column with name '{sample_id_column}')")

        # check duplicates
        csv_table.sample_id_column = sample_id_column
        sample_ids_list = csv_table.get_sample_ids()
        sample_ids_set = set(sample_ids_list)
        contains_duplicates = len(sample_ids_list) != len(sample_ids_set)
        if contains_duplicates:
            raise BadRequestException(
                f"Cannot import MetadataTable. The list of sample ids contains duplicates")

        return csv_table

# ####################################################################
#
# MetadataTableExporter class
#
# ####################################################################


@exporter_decorator("MetadataTableExporter", source_type=MetadataTable)
class MetadataTableExporter(TableExporter):
    config_specs: ConfigSpecs = {
        'file_name': StrParam(optional=True, short_description="File name (without extension)"),
        'file_format':
        StrParam(
            optional=True, default_value=Table.DEFAULT_FILE_FORMAT, allowed_values=Table.ALLOWED_FILE_FORMATS,
            short_description="File format"),
        'delimiter':
        StrParam(
            allowed_values=Table.ALLOWED_DELIMITER, default_value=Table.DEFAULT_DELIMITER,
            short_description="Delimiter character. Only for CSV files")}

    async def export_to_path(self, source: MetadataTable, dest_dir: str, params: ConfigParams, target_type: Type[File]) -> File:
        params["write_header"] = True
        params["write_index"] = False
        return await super().export_to_path(source, dest_dir, params, target_type)
