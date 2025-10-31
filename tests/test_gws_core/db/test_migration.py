

from gws_core import BaseTestCase
from gws_core.core.db.gws_core_db_manager import GwsCoreDbManager
from gws_core.core.db.migration.brick_migrator import (BrickMigration,
                                                       BrickMigrator,
                                                       MigrationObject)
from gws_core.core.db.migration.sql_migrator import SqlMigrator
from gws_core.core.db.version import Version, VersionInvalidException


class MigrationTest(BrickMigration):
    pass


class MigrationError(BrickMigration):
    @classmethod
    def migrate(cls, sql_migrator: SqlMigrator, from_version: Version, to_version: Version) -> None:
        raise Exception()


# test_migration
class TestMigration(BaseTestCase):

    def test_version(self):

        self.assertEqual(Version('1.0.0'), Version('1.0.0'))
        self.assertGreater(Version('2.0.0'), Version('1.0.0'))
        self.assertGreater(Version('1.1.0'), Version('1.0.0'))
        self.assertGreater(Version('1.0.1'), Version('1.0.0'))
        self.assertLess(Version('1.0.0-beta.1'), Version('1.0.0'))

        version: Version = Version('1.2.0-beta.1')

        self.assertEqual(version.major, 1)
        self.assertEqual(version.minor, 2)
        self.assertEqual(version.patch, 0)
        self.assertEqual(version.sub_patch, 1)
        self.assertEqual(str(version),  '1.2.0-beta.1')

        version_3: Version = Version('1.3.0')

        # Test sorting versions
        version_4: Version = Version('1.0.0')
        version_5: Version = Version('2.0.0')
        version_6: Version = Version('1.10.0')
        sorted_version = [version_4, version_3, version, version_5, version_6]
        sorted_version.sort()
        self.assertEqual(sorted_version, [
                         version_4, version, version_3, version_6, version_5])

        with self.assertRaises(VersionInvalidException):
            Version('1.2')

        with self.assertRaises(VersionInvalidException):
            Version('1.-2.0')

        with self.assertRaises(VersionInvalidException):
            Version('1.2.a')

        with self.assertRaises(VersionInvalidException):
            Version('1.2.2-beta.a')

    def test_brick_migrator(self):

        brick_migrator: BrickMigrator = BrickMigrator(
            'gws_core_test', Version('1.0.0'))
        db_manager = GwsCoreDbManager.get_instance()
        migration_v120 = MigrationObject(MigrationTest, Version('1.2.0'), '', False, db_manager)
        brick_migrator.append_migration(migration_v120)
        brick_migrator.append_migration(
            MigrationObject(MigrationTest, Version('1.0.0'), '', False, db_manager))
        brick_migrator.append_migration(
            MigrationObject(MigrationTest, Version('1.0.1'), '', False, db_manager))
        brick_migrator.append_migration(
            MigrationObject(MigrationTest, Version('2.0.1'), '', False, db_manager))

        # check that the migration list is in order and without the 1.0.0
        to_migrate = brick_migrator.get_to_migrate_list(db_manager)
        self.assertEqual(to_migrate[0].version,  Version('1.0.1'))
        self.assertEqual(to_migrate[1].version,  Version('1.2.0'))
        self.assertEqual(to_migrate[2].version,  Version('2.0.1'))

        # Append a version that already exists
        with self.assertRaises(Exception):
            brick_migrator.append_migration(migration_v120)

        # Check that the migrate worked and update brick version
        brick_migrator.migrate(db_manager)
        self.assertEqual(brick_migrator.current_brick_version,
                         Version('2.0.1'))
