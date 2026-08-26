import os

from gws_core.core.exception.exceptions.bad_request_exception import BadRequestException
from gws_core.impl.rich_text.rich_text_file_service import RichTextFileService
from gws_core.impl.rich_text.rich_text_types import RichTextObjectType
from gws_core.test.base_test_case_light import BaseTestCaseLight
from PIL import Image

# test_rich_text_file_service


class TestRichTextFileService(BaseTestCaseLight):
    """Test the storage of the rich text files.

    The object type is a plain str so other bricks can store the files of their own objects
    (ex: gws_project's 'project_document'), it is not restricted to RichTextObjectType.
    """

    def test_object_dir_path_with_custom_object_type(self):
        """A brick specific object type is stored in its own directory."""
        dir_path = RichTextFileService.get_object_dir_path("project_document", "doc-id-1")

        self.assertTrue(dir_path.endswith(os.path.join("project_document", "doc-id-1")))

    def test_object_dir_path_with_object_type_enum(self):
        """RichTextObjectType inherits str, so its members are still usable directly and
        are resolved to their value (not to 'RichTextObjectType.NOTE')."""
        enum_path = RichTextFileService.get_object_dir_path(RichTextObjectType.NOTE, "note-id-1")
        str_path = RichTextFileService.get_object_dir_path("note", "note-id-1")

        self.assertEqual(enum_path, str_path)
        self.assertTrue(enum_path.endswith(os.path.join("note", "note-id-1")))

    def test_object_dir_path_refuses_note_resource(self):
        with self.assertRaises(BadRequestException):
            RichTextFileService.get_object_dir_path(RichTextObjectType.NOTE_RESOURCE, "id-1")

        # the guard must also work when the type is provided as a plain string
        with self.assertRaises(BadRequestException):
            RichTextFileService.get_object_dir_path("note_resource", "id-1")

    def test_object_dir_path_refuses_invalid_segments(self):
        """The object type and id are directory names coming from the request url, they must
        not be able to escape the rich text directory."""
        invalid_values = ["../../etc", "a/b", "..", "", "with space", "dot.dot"]

        for invalid_value in invalid_values:
            with self.assertRaises(BadRequestException):
                RichTextFileService.get_object_dir_path(invalid_value, "doc-id-1")

            with self.assertRaises(BadRequestException):
                RichTextFileService.get_object_dir_path("project_document", invalid_value)

    def test_object_file_path_refuses_filename_escaping_the_object_dir(self):
        """The filename comes from the request url and the image route is public, so it must
        not be able to point at a file outside of the object directory."""
        invalid_filenames = [
            "../../../etc/passwd",
            "..",
            ".",
            "/etc/passwd",
            "sub/dir.png",
            "a/../../b.png",
            "..\\..\\win.ini",
            "",
        ]

        for invalid_filename in invalid_filenames:
            with self.assertRaises(BadRequestException):
                RichTextFileService.get_object_file_path(
                    "project_document", "doc-id-1", invalid_filename
                )

    def test_object_file_path_keeps_uploaded_file_names(self):
        """Uploaded files keep their original name (write_file), so a name with a space or an
        accent must still resolve, inside the object directory."""
        object_dir = RichTextFileService.get_object_dir_path("project_document", "doc-id-1")

        for filename in ["my report.pdf", "résumé.pdf", "file-1.tar.gz", "image.jpeg"]:
            file_path = RichTextFileService.get_object_file_path(
                "project_document", "doc-id-1", filename
            )

            self.assertEqual(file_path, os.path.join(object_dir, filename))

    def test_save_and_delete_image_of_custom_object_type(self):
        """An image of a brick specific object is saved in the object directory and the
        directory is deleted with the object."""
        object_type = "project_document"
        object_id = "doc-id-2"

        image = Image.new("RGB", (12, 7), color="red")
        result = RichTextFileService.save_image(object_type, object_id, image, "png")

        self.assertEqual(result.width, 12)
        self.assertEqual(result.height, 7)

        file_path = RichTextFileService.get_figure_file_path(object_type, object_id, result.filename)
        self.assertTrue(os.path.exists(file_path))

        # deleting the object dir removes the images (called when the object is deleted)
        RichTextFileService.delete_object_dir(object_type, object_id)
        self.assertFalse(os.path.exists(file_path))
