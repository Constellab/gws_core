# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from gws_core.impl.file.file import File
from gws_core.impl.table.table import Table
from gws_core.impl.table.encoding.encoding_table import EncodingTable
from gws_core.impl.table.metadata_table.metadata_table import MetadataTable
from gws_core.impl.table.tasks.table_exporter import TableExporter
from gws_core.impl.table.tasks.table_importer import TableImporter
from gws_core.resource.resource_decorator import resource_decorator
from gws_core.task.converter.exporter import exporter_decorator
from gws_core.task.converter.importer import importer_decorator


@resource_decorator("EncodedTable", hide=True, deprecated_since='0.3.3', deprecated_message="Use table instead")
class EncodedTable(Table):
    pass


@importer_decorator("EncodedTableImporter", target_type=EncodedTable, supported_extensions=Table.ALLOWED_FILE_FORMATS,
                    hide=True, deprecated_since='0.3.3', deprecated_message="Use table importer instead")
class EncodedTableImporter(TableImporter):
    pass


@exporter_decorator("EncodingTableExporter", source_type=EncodingTable, hide=True, deprecated_since='0.3.3',
                    deprecated_message='Use table exporter instead')
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
class MetadataTableFile(File):
    pass
