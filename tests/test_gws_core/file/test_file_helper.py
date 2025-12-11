from unittest import TestCase

from gws_core.impl.file.file_helper import FileHelper


# test_file_helper
class TestFileHelper(TestCase):
    def test_sanitizer(self):
        self.assertEqual(FileHelper.sanitize_name("\"Az02'{([$*!%?-_/.txt"), "Az02-_/.txt")

        # Test path traversal prevention
        self.assertEqual(FileHelper.sanitize_name("../../../etc/passwd"), "etc/passwd")

        # Test null byte and control character removal
        self.assertEqual(FileHelper.sanitize_name("file\x00name\x01.txt"), "filename.txt")

        # Test empty/dangerous inputs
        self.assertEqual(FileHelper.sanitize_name(".."), "sanitized_file")
        self.assertEqual(FileHelper.sanitize_name(""), "")

        # Test extension normalization to lowercase
        self.assertEqual(FileHelper.sanitize_name("file.TXT"), "file.txt")
        self.assertEqual(FileHelper.sanitize_name("document.CSV"), "document.csv")
        self.assertEqual(FileHelper.sanitize_name("image.JPG"), "image.jpg")

        # Test .R extension stays uppercase
        self.assertEqual(FileHelper.sanitize_name("script.r"), "script.R")
        self.assertEqual(FileHelper.sanitize_name("script.R"), "script.R")

        # Test compound extensions with .tar
        self.assertEqual(FileHelper.sanitize_name("archive.TAR.GZ"), "archive.tar.gz")
        self.assertEqual(FileHelper.sanitize_name("backup.tar.bz2"), "backup.tar.bz2")
        self.assertEqual(FileHelper.sanitize_name("data.TAR.XZ"), "data.tar.xz")

        # Test files with dots in name
        self.assertEqual(FileHelper.sanitize_name("my.file.TXT"), "my.file.txt")
        self.assertEqual(FileHelper.sanitize_name("test.data.CSV"), "test.data.csv")

        # Test mixed case compound extension
        self.assertEqual(FileHelper.sanitize_name("FILE.Tar.Gz"), "FILE.tar.gz")

    def test_get_extension(self):
        # Test normal extensions
        self.assertEqual(FileHelper.get_normalized_extension("file.txt"), "txt")
        self.assertEqual(FileHelper.get_normalized_extension("document.csv"), "csv")

        # Test uppercase normalization
        self.assertEqual(FileHelper.get_normalized_extension("file.TXT"), "txt")
        self.assertEqual(FileHelper.get_normalized_extension("IMAGE.JPG"), "jpg")

        # Test .R stays uppercase
        self.assertEqual(FileHelper.get_normalized_extension("script.r"), "R")
        self.assertEqual(FileHelper.get_normalized_extension("script.R"), "R")

        # Test compound extensions
        self.assertEqual(FileHelper.get_normalized_extension("archive.tar.gz"), "tar.gz")
        self.assertEqual(FileHelper.get_normalized_extension("backup.tar.bz2"), "tar.bz2")
        self.assertEqual(FileHelper.get_normalized_extension("data.TAR.XZ"), "tar.xz")

        # Test files with dots in name
        self.assertEqual(FileHelper.get_normalized_extension("my.file.txt"), "txt")
        self.assertEqual(FileHelper.get_normalized_extension("test.data.tar.gz"), "tar.gz")

        # Test no extension
        self.assertIsNone(FileHelper.get_normalized_extension("noextension"))
        self.assertIsNone(FileHelper.get_normalized_extension("folder/"))

    def test_get_name(self):
        # Test normal files
        self.assertEqual(FileHelper.get_name_without_extension("file.txt"), "file")
        self.assertEqual(FileHelper.get_name_without_extension("document.csv"), "document")

        # Test compound extensions - should remove all parts
        self.assertEqual(FileHelper.get_name_without_extension("archive.tar.gz"), "archive")
        self.assertEqual(FileHelper.get_name_without_extension("backup.tar.bz2"), "backup")
        self.assertEqual(FileHelper.get_name_without_extension("data.TAR.XZ"), "data")

        # Test files with dots in name
        self.assertEqual(FileHelper.get_name_without_extension("my.file.txt"), "my.file")
        self.assertEqual(FileHelper.get_name_without_extension("test.data.tar.gz"), "test.data")
        self.assertEqual(FileHelper.get_name_without_extension("my.test.file.csv"), "my.test.file")

        # Test no extension
        self.assertEqual(FileHelper.get_name_without_extension("noextension"), "noextension")
