from typing import cast

from gws_core.impl.file.file import File
from gws_core.impl.table.table import Table
from gws_core.resource.resource_dto import ResourceOrigin
from gws_core.resource.resource_model import ResourceModel
from gws_core.resource.resource_set.resource_set import ResourceSet
from gws_core.resource.task.resource_zipper_task import ResourceUnZipper, ResourceZipperTask
from gws_core.task.task_runner import TaskRunner
from gws_core.test.base_test_case import BaseTestCase
from pandas import DataFrame


# test_resource_zipper_loader
class TestResourceZipperLoader(BaseTestCase):
    def test_zip_and_load_table(self):
        """Test zipping a Table resource and loading it back."""
        # Create and save a Table resource
        table = Table(DataFrame({"col_a": [1, 2, 3], "col_b": [4, 5, 6]}))
        ResourceModel.save_from_resource(table, ResourceOrigin.UPLOADED)

        # Zip the table using ResourceZipperTask
        zip_runner = TaskRunner(ResourceZipperTask, inputs={"source": table})
        zip_outputs = zip_runner.run()
        zip_file: File = cast(File, zip_outputs["target"])

        self.assertIsInstance(zip_file, File)
        self.assertTrue(zip_file.exists())

        # Unzip and load using ResourceUnZipper
        unzip_runner = TaskRunner(ResourceUnZipper, inputs={"source": zip_file})
        unzip_outputs = unzip_runner.run()
        loaded_resource = unzip_outputs["target"]

        # Verify the loaded resource is a Table with the same data
        self.assertIsInstance(loaded_resource, Table)
        loaded_table: Table = cast(Table, loaded_resource)
        self.assertEqual(loaded_table.nb_rows, 3)
        self.assertEqual(loaded_table.nb_columns, 2)
        self.assertEqual(list(loaded_table.column_names), ["col_a", "col_b"])
        self.assertEqual(loaded_table.get_column_data("col_a"), [1, 2, 3])
        self.assertEqual(loaded_table.get_column_data("col_b"), [4, 5, 6])

    def test_zip_and_load_resource_set(self):
        """Test zipping a ResourceSet with sub-resources and loading it back."""
        # Create and save sub-resources
        table_1 = Table(DataFrame({"x": [10, 20]}))
        ResourceModel.save_from_resource(table_1, ResourceOrigin.UPLOADED)

        table_2 = Table(DataFrame({"y": [30, 40, 50]}))
        ResourceModel.save_from_resource(table_2, ResourceOrigin.UPLOADED)

        # Create and save a ResourceSet containing the two tables
        resource_set = ResourceSet()
        resource_set.add_resource(table_1, unique_name="table_1", create_new_resource=False)
        resource_set.add_resource(table_2, unique_name="table_2", create_new_resource=False)
        resource_model = ResourceModel.save_from_resource(resource_set, ResourceOrigin.UPLOADED)

        resource_set2 = resource_model.get_resource(new_instance=True)

        # Zip the ResourceSet using ResourceZipperTask
        zip_runner = TaskRunner(ResourceZipperTask, inputs={"source": resource_set2})
        zip_outputs = zip_runner.run()
        zip_file: File = cast(File, zip_outputs["target"])

        self.assertIsInstance(zip_file, File)
        self.assertTrue(zip_file.exists())

        # Unzip and load using ResourceUnZipper
        unzip_runner = TaskRunner(ResourceUnZipper, inputs={"source": zip_file})
        unzip_outputs = unzip_runner.run()
        loaded_resource = unzip_outputs["target"]

        # Verify the loaded resource is a ResourceSet
        self.assertIsInstance(loaded_resource, ResourceSet)
        loaded_set: ResourceSet = cast(ResourceSet, loaded_resource)

        # Verify sub-resources are present
        resources = loaded_set.get_resources()
        self.assertEqual(len(resources), 2)
        self.assertTrue(loaded_set.resource_exists("table_1"))
        self.assertTrue(loaded_set.resource_exists("table_2"))

        # Verify sub-resource data
        loaded_table_1: Table = cast(Table, loaded_set.get_resource("table_1"))
        self.assertIsInstance(loaded_table_1, Table)
        self.assertEqual(loaded_table_1.nb_rows, 2)
        self.assertEqual(list(loaded_table_1.column_names), ["x"])
        self.assertEqual(loaded_table_1.get_column_data("x"), [10, 20])

        loaded_table_2: Table = cast(Table, loaded_set.get_resource("table_2"))
        self.assertIsInstance(loaded_table_2, Table)
        self.assertEqual(loaded_table_2.nb_rows, 3)
        self.assertEqual(list(loaded_table_2.column_names), ["y"])
        self.assertEqual(loaded_table_2.get_column_data("y"), [30, 40, 50])
