import os
from runpy import run_path
from typing import Any, Literal

from gws_core.config.param.code_param.python_code_param import PythonCodeParam
from gws_core.config.param.param_spec import BoolParam
from gws_core.core.utils.settings import Settings
from gws_core.impl.file.file_helper import FileHelper


class AgentCodeHelper:
    @classmethod
    def run_python_code(cls, code: str, params: dict[str, Any]) -> dict[str, Any]:
        temp_folder = Settings.make_temp_dir()
        snippet_filepath = os.path.join(temp_folder, "snippet.py")
        with open(snippet_filepath, "w", encoding="utf-8") as file_path:
            file_path.write(code)

        try:
            global_vars = run_path(snippet_filepath, init_globals=params)
        finally:
            FileHelper.delete_dir(temp_folder)

        return global_vars

    @classmethod
    def compute_text_params(cls, params: list[str]) -> dict[str, Any]:
        """Compute text that declare variables to actuals variables.
        Ex : ["a = 1", "b = A"] -> {"a": 1, "b": "A"}

        :param params: _description_
        :type params: List[str]
        :raises Exception: _description_gf
        :return: _description_
        :rtype: Dict[str, Any]
        """
        result: dict[str, Any] = {}
        if params:
            params_str: str = "\n".join(params)
            try:
                exec(params_str, {}, result)
            except Exception as err:
                raise Exception("Cannot parse parameters") from err

        return result

    @classmethod
    def get_python_code_template(cls) -> str:
        return cls._read_template("py_live_snippet_template.py", "code")

    @classmethod
    def get_python_env_code_template(cls) -> str:
        return cls._read_template("py_env_snippet_template.py", "code")

    @classmethod
    def get_r_code_template(cls) -> str:
        return cls._read_template("r_env_snippet_template.R", "code")

    @classmethod
    def get_streamlit_code_template(cls) -> str:
        return cls._read_template("streamlit_agent_template.py", "code")

    @classmethod
    def get_streamlit_env_code_template(cls) -> str:
        return cls._read_template("streamlit_env_agent_template.py", "code")

    @classmethod
    def get_pip_env_file_template(cls) -> str:
        return cls._read_template("env_pipenv.txt", "env")

    @classmethod
    def get_conda_env_file_template(cls) -> str:
        return cls._read_template("env_py_conda.yml", "env")

    @classmethod
    def get_r_conda_env_file_template(cls) -> str:
        return cls._read_template("env_r_conda.yml", "env")

    @classmethod
    def get_streamlit_conda_env_file_template(cls) -> str:
        return cls._read_template("env_streamlit_conda.yml", "env")

    @classmethod
    def get_streamlit_pip_env_file_template(cls) -> str:
        return cls._read_template("env_streamlit_pipenv.txt", "env")

    @classmethod
    def _read_template(cls, file_name: str, template_type: Literal["code", "env"]) -> str:
        template_folder = (
            "../_templates/code" if template_type == "code" else "../_templates/env_config"
        )

        cdir = os.path.dirname(os.path.abspath(__file__))
        template_file_path = os.path.join(cdir, template_folder, f"{file_name}")
        with open(template_file_path, encoding="utf-8") as file_path:
            content = file_path.read()
        return content

    @classmethod
    def get_streamlit_code_param(cls, is_env: bool = False) -> PythonCodeParam:
        """Get the code parameter for the streamlit agent."""
        return PythonCodeParam(
            default_value=cls.get_streamlit_code_template()
            if not is_env
            else cls.get_streamlit_env_code_template(),
            human_name="Streamlit app code",
            short_description="Code of the streamlit app to run",
        )

    @classmethod
    def get_streamlit_requires_auth_param(cls) -> BoolParam:
        """Get the requires authentication parameter for the streamlit agent."""
        return BoolParam(
            default_value=True,
            visibility="protected",
            human_name="Requires authentication",
            short_description="If the app requires authentication",
        )
