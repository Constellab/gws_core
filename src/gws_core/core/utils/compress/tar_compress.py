import os
import shutil
import subprocess
import tempfile

from .compress import Compress


class TarCompress(Compress):
    """Class to compress and uncompress tar file using system `tar` via subprocess.

    Entries are staged as symlinks in a temp directory so that arcnames can be
    customized without copying data, then archived in a single `tar` invocation.
    """

    compress_option: str = ""
    tar_create_flags: list[str] = []
    tar_extract_flags: list[str] = []

    _staging_dir: str

    def __init__(self, destination_file_path: str):
        super().__init__(destination_file_path)
        self._staging_dir = tempfile.mkdtemp(prefix="tar_stage_")

    def add_dir(self, dir_path: str, dir_name: str | None = None) -> None:
        dir_name = self._generate_node_name(dir_path, dir_name)
        self._stage(dir_path, dir_name)

    def add_file(self, file_path: str, file_name: str | None = None) -> None:
        file_name = self._generate_node_name(file_path, file_name)
        self._stage(file_path, file_name)

    def _stage(self, source_path: str, arcname: str) -> None:
        safe_arcname = self.sanitize_arcname(arcname)
        link_path = os.path.join(self._staging_dir, safe_arcname)
        staging_root = os.path.realpath(self._staging_dir)
        resolved_parent = os.path.realpath(os.path.dirname(link_path))
        if (
            resolved_parent != staging_root
            and not resolved_parent.startswith(staging_root + os.sep)
        ):
            raise ValueError(
                f"Invalid arcname '{arcname}': resolves outside the staging directory."
            )
        parent = os.path.dirname(link_path)
        if parent and parent != self._staging_dir:
            os.makedirs(parent, exist_ok=True)
        os.symlink(os.path.abspath(source_path), link_path)

    def close(self) -> str:
        try:
            entries = sorted(os.listdir(self._staging_dir))
            cmd = [
                "tar",
                "-c",
                "-h",  # follow symlinks
                *self.tar_create_flags,
                "-f",
                self.destination_file_path,
                "-C",
                self._staging_dir,
                *entries,
            ]
            subprocess.run(cmd, check=True)
        finally:
            shutil.rmtree(self._staging_dir, ignore_errors=True)
        return self.destination_file_path

    @classmethod
    def decompress(cls, file_path: str, destination_folder: str) -> None:
        """Uncompress a tar archive into destination_folder."""
        os.makedirs(destination_folder, exist_ok=True)
        cmd = [
            "tar",
            "-x",
            *cls.tar_extract_flags,
            "-f",
            file_path,
            "-C",
            destination_folder,
        ]
        subprocess.run(cmd, check=True)

    @classmethod
    def can_uncompress_file(cls, file_path: str) -> bool:
        """Return true if the file can be uncompressed by this class"""
        return file_path.endswith(".tar")

    @classmethod
    def get_supported_extensions(cls) -> set:
        """Return the list of supported extensions"""
        return {"tar"}

    @classmethod
    def get_names(cls, file_path: str) -> list[str]:
        """Return the list of entry names inside the tar archive."""
        cmd = ["tar", "-t", *cls.tar_extract_flags, "-f", file_path]
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        return [line.rstrip("/") for line in result.stdout.splitlines() if line]

    @classmethod
    def is_tar_file(cls, file_path: str) -> bool:
        """Return true if the file is a valid tar archive readable by system tar."""
        if not os.path.isfile(file_path):
            return False
        cmd = ["tar", "-t", *cls.tar_extract_flags, "-f", file_path]
        result = subprocess.run(cmd, capture_output=True, check=False)
        return result.returncode == 0


class TarGzCompress(TarCompress):
    """Class to compress and uncompress tar.gz file using system `tar`."""

    compress_option: str = ":gz"
    tar_create_flags: list[str] = ["-I", "pigz"]
    tar_extract_flags: list[str] = ["-I", "pigz"]

    @classmethod
    def can_uncompress_file(cls, file_path: str) -> bool:
        """Return true if the file can be uncompressed by this class"""
        return file_path.endswith(".tar.gz")

    @classmethod
    def get_supported_extensions(cls) -> set:
        """Return the list of supported extensions"""
        return {"tar.gz"}
