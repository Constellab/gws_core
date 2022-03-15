# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from gws_core.deprecated.dep_table_file import TableFile
from gws_core.impl.table.encoding.encoded_table import EncodedTable
from gws_core.impl.table.encoding.encoding_table import EncodingTable
from gws_core.impl.table.metadata_table.metadata_table import MetadataTable
from gws_core.impl.table.tasks.table_exporter import TableExporter
from gws_core.resource.resource_decorator import resource_decorator
from gws_core.task.converter.exporter import exporter_decorator


@exporter_decorator("EncodingTableExporter", source_type=EncodingTable, hide=True, deprecated_since='0.3.3',
                    deprecated_message='Use table exporter')
class EncodingTableExporter(TableExporter):
    pass


@exporter_decorator("EncodedTableExporter", source_type=EncodedTable, hide=True, deprecated_since='0.3.3',
                    deprecated_message='Use table exporter')
class EncodedTableExporter(TableExporter):
    pass


@resource_decorator("MetadataTableFile",
                    human_name="MetadataTable file",
                    short_description="Table file of metadata", hide=True, deprecated_since='0.3.3',
                    deprecated_message='Use table file instead')
class MetadataTableFile(TableFile):
    pass


@exporter_decorator("MetadataTableExporter", source_type=MetadataTable, hide=True, deprecated_since='0.3.3',
                    deprecated_message='Use table exporter instead')
class MetadataTableExporter(TableExporter):
    pass
