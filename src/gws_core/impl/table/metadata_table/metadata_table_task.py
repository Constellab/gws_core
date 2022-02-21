# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import Type

from ....config.config_types import ConfigParams, ConfigSpecs
from ....config.param_spec import StrParam
from ....core.exception.exceptions import BadRequestException
from ....task.converter.exporter import exporter_decorator
from ....task.converter.importer import importer_decorator
from ..tasks.table_exporter import TableExporter
from ..tasks.table_importer import TableImporter
from .metadata_table import MetadataTable, MetadataTableFile

# ####################################################################
#
# Importer class
#
# ####################################################################


@importer_decorator("MetadataTableImporter", source_type=MetadataTableFile, target_type=MetadataTable)
class MetadataTableImporter(TableImporter):

    config_specs: ConfigSpecs = {
        **TableImporter.config_specs,
        'sample_id_column':
        StrParam(
            default_value=MetadataTable.DEFAULT_SAMPLE_ID_COLUMN,
            short_description="The name of the column containing the sample ids"), }

    async def import_from_path(self, file: MetadataTableFile, params: ConfigParams, target_type: Type[MetadataTable]) -> MetadataTable:
        """
        Import from a repository

        :param file: The file to import
        :type file: `MetadataTableFile`
        :param params: The config params
        :type params: `ConfigParams`
        :returns: the parsed metadata
        :rtype: MetadataTable
        """

        params["index_column"] = None
        params["comment"] = "#"
        csv_table: MetadataTable = await super().import_from_path(file, params, target_type)
        sample_id_column = params.get_value("sample_id_column", MetadataTable.DEFAULT_SAMPLE_ID_COLUMN)

        if not csv_table.column_exists(sample_id_column):
            raise BadRequestException(
                f"Cannot import MetadataTable. No sample-id column found (no column with name '{sample_id_column}')")

        csv_table.sample_id_column = sample_id_column

        # check duplicates
        sample_ids_list = csv_table.get_sample_ids()
        sample_ids_set = set(sample_ids_list)
        contains_duplicates = len(sample_ids_list) != len(sample_ids_set)
        if contains_duplicates:
            raise BadRequestException(
                f"Cannot import MetadataTable. The list of sample ids contains duplicates")

        return csv_table


# ####################################################################
#
# Exporter class
#
# ####################################################################


@ exporter_decorator("MetadataTableExporter", source_type=MetadataTable, target_type=MetadataTableFile)
class MetadataTableExporter(TableExporter):
    pass
