# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from gws_core.experiment.experiment import Experiment
from gws_core.impl.file.fs_node_model import FSNodeModel
from gws_core.lab.lab_config_model import LabConfigModel
from gws_core.model.typing import Typing
from gws_core.report.report import Report
from peewee import BigIntegerField
from playhouse.migrate import MySQLMigrator, migrate

from ...utils.logger import Logger
from ..brick_migrator import BrickMigration
from ..db_migration import brick_migration
from ..version import Version


@brick_migration('0.2.2')
class Migration022(BrickMigration):

    @classmethod
    def migrate(cls, from_version: Version, to_version: Version) -> None:

        Logger.info('Adding deprecated columns to Typing')
        migrator = MySQLMigrator(Typing.get_db_manager().db)

        migrate(
            migrator.add_column(
                Typing.get_table_name(),
                Typing.deprecated_since.column_name, Typing.deprecated_since),
            migrator.add_column(
                Typing.get_table_name(),
                Typing.deprecated_message.column_name, Typing.deprecated_message),
        )


@brick_migration('0.2.3')
class Migration023(BrickMigration):

    @classmethod
    def migrate(cls, from_version: Version, to_version: Version) -> None:

        Logger.info('Create LabConfigModel table and add lab_config_id to experiment')
        migrator = MySQLMigrator(Typing.get_db_manager().db)

        LabConfigModel.create_table()
        migrate(
            migrator.add_column(
                Experiment.get_table_name(),
                Experiment.lab_config.column_name, Experiment.lab_config)
        )


@brick_migration('0.3.3')
class Migration033(BrickMigration):

    @classmethod
    def migrate(cls, from_version: Version, to_version: Version) -> None:

        Logger.info('Create symbolic link in FsNodeModel and convert size to BigInt')
        migrator = MySQLMigrator(FSNodeModel.get_db_manager().db)

        migrate(
            migrator.add_column(
                FSNodeModel.get_table_name(),
                FSNodeModel.is_symbolic_link.column_name, FSNodeModel.is_symbolic_link),

            migrator.alter_column_type(FSNodeModel.get_table_name(), FSNodeModel.size.column_name,
                                       BigIntegerField(null=True))
        )


@brick_migration('0.3.8')
class Migration038(BrickMigration):

    @classmethod
    def migrate(cls, from_version: Version, to_version: Version) -> None:

        Logger.info('Create lab config column in report table')
        migrator = MySQLMigrator(FSNodeModel.get_db_manager().db)

        migrate(
            migrator.add_column(
                Report.get_table_name(),
                Report.lab_config.column_name, Report.lab_config),
        )
