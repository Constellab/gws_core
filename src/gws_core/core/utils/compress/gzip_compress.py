import os
import subprocess

from gws_core.impl.file.file_helper import FileHelper

from .compress import Compress


class GzipCompress(Compress):
    """Class to compress and uncompress .gz file using system `pigz` (parallel gzip)."""

    supports_multiple_entries: bool = False

    file_path: str | None = None

    def add_dir(self, dir_path: str, dir_name: str | None = None) -> None:
        raise Exception("GzipCompress does not support directory")

    def add_file(self, file_path: str, file_name: str | None = None) -> None:
        if self.file_path is not None:
            raise Exception("GzipCompress does not support multiple file")
        self.file_path = file_path

    def close(self) -> str:
        if self.file_path is None:
            raise Exception("No file added to the GzipCompress")

        with open(self.file_path, "rb") as input_file, open(self.destination_file_path, "wb") as output_file:
            subprocess.run(["pigz", "-c"], stdin=input_file, stdout=output_file, check=True)

        return self.destination_file_path

    @classmethod
    def decompress(cls, file_path: str, destination_folder: str) -> None:
        """Uncompress a .gz file into destination_folder as a .txt file."""
        file_name = FileHelper.get_name_without_extension(file_path) + ".txt"
        decompress_file_path = os.path.join(destination_folder, file_name)

        FileHelper.create_dir_if_not_exist(destination_folder)

        with open(file_path, "rb") as f_in, open(decompress_file_path, "wb") as f_out:
            subprocess.run(["pigz", "-d", "-c"], stdin=f_in, stdout=f_out, check=True)

    @classmethod
    def can_uncompress_file(cls, file_path: str) -> bool:
        """Return true if the file can be uncompressed by this class"""
        if file_path.endswith(".tar.gz"):
            return False
        return file_path.endswith(".gz")

    @classmethod
    def get_supported_extensions(cls) -> set:
        """Return the list of supported extensions"""
        return {"gz"}
