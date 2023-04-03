# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from runpy import run_path
from tempfile import mkstemp
from typing import Any, Dict

from gws_core.impl.file.file_helper import FileHelper


class LiveCodeHelper:

    @classmethod
    def run_python_code(cls, code: str, params: Dict[str, Any]) -> Dict[str, Any]:

        _, snippet_filepath = mkstemp(suffix=".py")
        with open(snippet_filepath, 'w', encoding="utf-8") as fp:
            fp.write(code)

        global_vars = run_path(snippet_filepath, init_globals=params)

        FileHelper.delete_file(snippet_filepath)

        return global_vars
