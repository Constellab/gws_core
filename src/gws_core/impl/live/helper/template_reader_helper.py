# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


import os


class TemplateReaderHelper:

    @classmethod
    def read_snippet_template(cls, file_name) -> str:
        cdir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(cdir, "../_templates/snippets", f"{file_name}")
        with open(file_path, encoding="utf-8") as fp:
            content = fp.read()
        return content

    @classmethod
    def read_env_config_template(cls, file_name) -> str:
        cdir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(cdir, "../_templates/env_configs", f"{file_name}")
        with open(file_path, encoding="utf-8") as fp:
            content = fp.read()
        return content
