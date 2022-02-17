

from gws_core import BaseTestCase
from gws_core.brick.brick_model import BrickModel
from gws_core.core.db.brick_migrator import BrickMigration, BrickMigrator
from gws_core.core.db.db_migration import DbMigrationService, brick_migration
from gws_core.core.db.version import Version, VersionInvalidException
from gws_core.core.utils.settings import ModuleInfo


class MigrationTest(BrickMigration):
    pass


@brick_migration('99.99.99')
class MigrationTest2(BrickMigration):
    pass


class MigrationError(BrickMigration):
    @classmethod
    def migrate(cls, from_version: Version, to_version: Version) -> None:
        raise Exception()


class TestMigration(BaseTestCase):

    def test_version(self):

        version: Version = Version('1.2.0')

        self.assertEqual(version.major, 1)
        self.assertEqual(version.minor, 2)
        self.assertEqual(version.patch, 0)
        self.assertEqual(version.get_version_as_int(), 120)

        version_2: Version = Version('1.2.0')
        version_3: Version = Version('1.3.0')

        self.assertEqual(version, version_2)
        self.assertNotEqual(version, version_3)
        self.assertGreater(version_3, version)
        self.assertGreaterEqual(version_3, version)
        self.assertLess(version, version_3)
        self.assertLessEqual(version, version_3)

        # Test sorting versions
        version_4: Version = Version('1.0.0')
        sorted_version = [version_4, version_3, version]
        sorted_version.sort()
        self.assertEqual(sorted_version, [version_4, version, version_3])

        with self.assertRaises(VersionInvalidException):
            Version('1.2')

        with self.assertRaises(VersionInvalidException):
            Version('1.-2.0')

    def test_brick_migrator(self):

        brick_migrator: BrickMigrator = BrickMigrator('gws_core_test', Version('1.0.0'))
        brick_migrator.append_migration(MigrationTest, Version('1.2.0'))
        brick_migrator.append_migration(MigrationTest, Version('1.0.0'))
        brick_migrator.append_migration(MigrationTest, Version('1.0.1'))
        brick_migrator.append_migration(MigrationTest, Version('2.0.1'))

        # check that the migration list is in order and without the 1.0.0
        to_migrate = brick_migrator._get_to_migrate_list()
        self.assertEqual(to_migrate[0].version,  Version('1.0.1'))
        self.assertEqual(to_migrate[1].version,  Version('1.2.0'))
        self.assertEqual(to_migrate[2].version,  Version('2.0.1'))

        # Append a version that already exists
        with self.assertRaises(Exception):
            brick_migrator.append_migration(MigrationTest, Version('2.0.1'))

        # Check that the migrate worked and update brick version
        brick_migrator.migrate()
        self.assertEqual(brick_migrator.current_brick_version, Version('2.0.1'))
