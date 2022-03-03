# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from gws_core.experiment.experiment import Experiment
from gws_core.model.typing import Typing
from playhouse.migrate import SqliteMigrator, migrate

from ...utils.logger import Logger
from ..brick_migrator import BrickMigration
from ..db_migration import brick_migration
from ..version import Version


@brick_migration('0.2.2')
class Migration022(BrickMigration):

    @classmethod
    def migrate(cls, from_version: Version, to_version: Version) -> None:

        Logger.info('Adding deprecated columns to Typing entity and lab_config_id to experiment')
        migrator = SqliteMigrator(Typing.get_db_manager().db)

        migrate(
            migrator.add_column(
                Typing.get_table_name(),
                Typing.deprecated_since.column_name, Typing.deprecated_since),
            migrator.add_column(
                Typing.get_table_name(),
                Typing.deprecated_message.column_name, Typing.deprecated_message),
            migrator.add_column(
                Experiment.get_table_name(),
                Experiment.lab_config.column_name, Experiment.lab_config)
        )
