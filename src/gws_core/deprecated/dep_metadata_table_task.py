# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import Type

from gws_core.impl.file.file import File

from ..config.config_types import ConfigParams, ConfigSpecs
from ..config.param.param_spec import StrParam
from ..core.exception.exceptions import BadRequestException
from ..impl.table.table import Table
from ..impl.table.tasks.table_exporter import TableExporter
from ..impl.table.tasks.table_importer import TableImporter
from ..task.converter.exporter import exporter_decorator
from ..task.converter.importer import importer_decorator
from .dep_metadata_table import MetadataTable

# ####################################################################
#
# Importer class
#
# ####################################################################


@importer_decorator("MetadataTableImporter", target_type=MetadataTable,
                    supported_extensions=Table.ALLOWED_FILE_FORMATS, deprecated_since="0.4.7",
                    deprecated_message="Use Table Importer instead", hide=True)
class MetadataTableImporter(TableImporter):

    config_specs: ConfigSpecs = {
        'delimiter':
        StrParam(
            allowed_values=Table.ALLOWED_DELIMITER, default_value=Table.DEFAULT_DELIMITER,
            human_name="Delimiter",
            short_description="Delimiter character. Only for parsing CSV files")
    }

    def import_from_path(self, source: File, params: ConfigParams, target_type: Type[MetadataTable]) -> MetadataTable:
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
        csv_table: MetadataTable = super().import_from_path(source, params, target_type)

        sample_id_column = csv_table.column_names[0]
        if not sample_id_column:
            raise BadRequestException(
                "Cannot import MetadataTable. A name is required for the sample_id column (i.e. the first column)")

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

            # find the duplicate
            unique_set = set()
            duplicates = []

            for sample_id in sample_ids_list:
                if sample_id in unique_set:
                    duplicates.append(sample_id)
                else:
                    unique_set.add(sample_id)
            raise BadRequestException(
                f"Cannot import MetadataTable. The following sample_ids are duplicated: {duplicates}")

        return csv_table

# ####################################################################
#
# MetadataTableExporter class
#
# ####################################################################


@exporter_decorator("MetadataTableExporter", source_type=MetadataTable, deprecated_since="0.4.7",
                    deprecated_message="Use Table Exporter instead", hide=True)
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

    def export_to_path(
            self, source: MetadataTable, dest_dir: str, params: ConfigParams, target_type: Type[File]) -> File:
        params["write_header"] = True
        params["write_index"] = False
        return super().export_to_path(source, dest_dir, params, target_type)