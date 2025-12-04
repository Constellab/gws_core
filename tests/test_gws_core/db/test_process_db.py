from unittest import TestCase

from gws_core.core.db.process_db import ProcessDb
from gws_core.core.model.model import Model
from peewee import CharField


class TestProcessTable(Model):
    id = CharField(primary_key=True, max_length=36)
    text = CharField()

    class Meta:
        table_name = "test_process_table"
        is_table = True


def _simple_select_and_insert(text: str):
    """Function to run in background process"""
    # Select existing records
    list(TestProcessTable.select())

    # Insert a new record
    TestProcessTable.create(id=text, text=f"processed_{text}")


# test_process_db
class TestProcessDb(TestCase):
    # clean the table and db connection after the test (required if other tests are run after)
    @classmethod
    def tearDownClass(cls):
        TestProcessTable.get_db_manager().close_db()
        TestProcessTable.drop_table()

    def test_process_db(self):
        """Test that ProcessDb properly resets db connection for background process"""
        TestProcessTable.drop_table()
        TestProcessTable.create_table()

        # Create initial records
        for i in range(0, 10):
            TestProcessTable.create(id=str(i), text=f"text_{i}")

        # Force opening the db before the process
        initial_count = TestProcessTable.select().count()
        self.assertEqual(initial_count, 10)

        # Start a background process that uses the db
        process = ProcessDb(target=_simple_select_and_insert, args=("new_record",))
        process.start()
        process.join()  # Wait for it to complete

        # Verify the process completed successfully
        self.assertEqual(process.exitcode, 0)

        # Verify the new record was created
        final_count = TestProcessTable.select().count()
        self.assertEqual(final_count, 11)

        # Verify the content of the new record
        new_record = TestProcessTable.get_by_id("new_record")
        self.assertEqual(new_record.text, "processed_new_record")

    def test_multiple_process_db(self):
        """Test running multiple ProcessDb instances"""
        TestProcessTable.drop_table()
        TestProcessTable.create_table()

        # Start multiple background processes
        processes = []
        for i in range(0, 5):
            process = ProcessDb(target=_simple_select_and_insert, args=(f"process_{i}",))
            process.start()
            processes.append(process)

        # Wait for all processes to complete
        for process in processes:
            process.join()
            self.assertEqual(process.exitcode, 0)

        # Verify all records were created
        final_count = TestProcessTable.select().count()
        self.assertEqual(final_count, 5)

        # Verify each record exists
        for i in range(0, 5):
            record = TestProcessTable.get_by_id(f"process_{i}")
            self.assertEqual(record.text, f"processed_process_{i}")
