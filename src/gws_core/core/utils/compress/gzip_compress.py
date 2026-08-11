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
            self._run_pigz(
                ["pigz", "-c"], input_file, output_file, "pigz compress", self.file_path
            )

        return self.destination_file_path

    @classmethod
    def decompress(cls, file_path: str, destination_folder: str) -> None:
        """Uncompress a .gz file into destination_folder as a .txt file."""
        file_name = FileHelper.get_name_without_extension(file_path) + ".txt"
        decompress_file_path = os.path.join(destination_folder, file_name)

        FileHelper.create_dir_if_not_exist(destination_folder)

        with open(file_path, "rb") as f_in, open(decompress_file_path, "wb") as f_out:
            cls._run_pigz(
                ["pigz", "-d", "-c"], f_in, f_out, "pigz decompress", file_path
            )

    @staticmethod
    def _run_pigz(cmd: list[str], stdin, stdout, action: str, file_path: str) -> None:
        """Run a pigz command, surfacing its stderr in the raised error.

        `pigz` signals a corrupt input and a failed write (quota, permissions, I/O error)
        through its exit code alone; without the captured stderr the caller cannot tell
        them apart. Output is streamed straight to ``stdout``, so a failure leaves a
        truncated file behind — the caller is responsible for discarding it.
        """
        try:
            subprocess.run(cmd, stdin=stdin, stdout=stdout, stderr=subprocess.PIPE,
                           check=True, text=True)
        except subprocess.CalledProcessError as e:
            raise RuntimeError(
                f"{action} failed on '{file_path}' (exit {e.returncode}): "
                f"{(e.stderr or '').strip()}"
            ) from e

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
