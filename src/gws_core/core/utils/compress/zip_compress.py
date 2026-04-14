import os
import shutil
import subprocess
import tempfile

from .compress import Compress


class ZipCompress(Compress):
    """
    Class to zip and unzip files and folders using system `zip` / `unzip`.

    Entries are staged as symlinks in a temp directory so arcnames can be
    customized without copying data, then archived in a single invocation.
    """

    _staging_dir: str

    def __init__(self, destination_file_path: str):
        super().__init__(destination_file_path)
        self._staging_dir = tempfile.mkdtemp(prefix="zip_stage_")

    def add_dir(self, dir_path: str, dir_name: str | None = None) -> None:
        dir_name = self._generate_node_name(dir_path, dir_name)
        self._stage(dir_path, dir_name)

    def add_file(self, file_path: str, file_name: str | None = None) -> None:
        file_name = self._generate_node_name(file_path, file_name)
        self._stage(file_path, file_name)

    def _stage(self, source_path: str, arcname: str) -> None:
        link_path = os.path.join(self._staging_dir, arcname)
        parent = os.path.dirname(link_path)
        if parent and parent != self._staging_dir:
            os.makedirs(parent, exist_ok=True)
        os.symlink(os.path.abspath(source_path), link_path)

    def close(self) -> str:
        try:
            entries = sorted(os.listdir(self._staging_dir))
            # -r recursive, -y store symlinks? no, we want to follow them: default `zip` follows symlinks to files,
            # and with -r it recurses into symlinked dirs as well.
            cmd = ["zip", "-r", "-q", self.destination_file_path, *entries]
            subprocess.run(cmd, check=True, cwd=self._staging_dir)
        finally:
            shutil.rmtree(self._staging_dir, ignore_errors=True)
        return self.destination_file_path

    @classmethod
    def decompress(cls, file_path: str, destination_folder: str) -> None:
        """Unzip a file into destination_folder."""
        os.makedirs(destination_folder, exist_ok=True)
        cmd = ["unzip", "-q", "-o", file_path, "-d", destination_folder]
        subprocess.run(cmd, check=True)

    @classmethod
    def can_uncompress_file(cls, file_path: str) -> bool:
        """Return true if the file can be uncompressed by this class"""
        return file_path.endswith(".zip")

    @classmethod
    def get_supported_extensions(cls) -> set:
        """Return the list of supported extensions"""
        return {"zip"}
