"""Helpers to inject a virtual environment in a generated app.

These helpers are shared by the Streamlit and Reflex app generators. They build the
template variables that add a ``get_shell_proxy()`` override to the generated
``generate_<name>.py`` task, and resolve the env file shipped for each env type.
"""

import os
import shutil

from gws_core import StringHelper
from gws_core.core.utils.gws_core_packages import GwsCorePackages
from gws_core.core.utils.package_helper import PackageHelper

from gws_cli.utils.cli_utils import CLIUtils

# Shell proxy class used for each env type: env_type -> (class name, import module)
ENV_SHELL_PROXY = {
    "PIP": ("PipShellProxy", "gws_core.impl.shell.pip_shell_proxy"),
    "CONDA": ("CondaShellProxy", "gws_core.impl.shell.conda_shell_proxy"),
    "MAMBA": ("MambaShellProxy", "gws_core.impl.shell.mamba_shell_proxy"),
}

# pip package providing each app type, used to pin the env file to the installed version
APP_TYPE_PACKAGE = {
    "streamlit": GwsCorePackages.STREAMLIT,
    "reflex": GwsCorePackages.REFLEX,
}

# Supported env types (excluding "NONE")
SUPPORTED_ENV_TYPES = list(ENV_SHELL_PROXY.keys())


def validate_env_type(env_type: str) -> str:
    """Normalize and validate a virtual environment type.

    :param env_type: env type provided by the user (case insensitive)
    :return: the upper case env type
    :raises ValueError: if the env type is not supported
    """
    env_type = env_type.upper()
    if env_type != "NONE" and env_type not in ENV_SHELL_PROXY:
        raise ValueError(
            f"Invalid env type '{env_type}'. Supported values: NONE, "
            f"{', '.join(SUPPORTED_ENV_TYPES)}."
        )
    return env_type


def get_env_file_name(app_type: str, env_type: str) -> str:
    """Return the env file name shipped for the given app and env type.

    :param app_type: "streamlit" or "reflex"
    :param env_type: "PIP", "CONDA" or "MAMBA"
    :return: env file name (e.g. "env_streamlit_mamba.yml")
    """
    extension = "txt" if env_type == "PIP" else "yml"
    return f"env_{app_type}_{env_type.lower()}.{extension}"


def copy_env_file(template_env_folder: str, app_type: str, env_type: str, dest_folder: str) -> str:
    """Copy the env file for the given env type into the app code folder.

    The env file is pinned to the version of the app package (streamlit / reflex)
    currently installed in the system, so the generated app runs the same version.

    :param template_env_folder: folder containing the env file templates
    :param app_type: "streamlit" or "reflex"
    :param env_type: "PIP", "CONDA" or "MAMBA"
    :param dest_folder: folder where the env file is copied (the app code folder)
    :raises ValueError: if the app package is not installed in the current environment
    :return: the env file name (relative to the app code folder)
    """
    env_file_name = get_env_file_name(app_type, env_type)
    env_file_path = os.path.join(dest_folder, env_file_name)
    shutil.copy2(os.path.join(template_env_folder, env_file_name), env_file_path)

    # Pin the env file to the version of the app package installed in the system
    package_version = PackageHelper.get_package_version(APP_TYPE_PACKAGE[app_type])
    CLIUtils.replace_vars_in_file(env_file_path, {"packageVersion": package_version})

    return env_file_name


def apply_env_app_overlay(overlay_folder: str, dest_folder: str) -> None:
    """Override the generated app code with the virtual environment variant.

    A virtual environment app cannot load ``gws_core``, so it must import from
    ``gws_streamlit_env_main`` / ``gws_reflex_env_main`` instead. This copies the
    env specific app code (e.g. ``main_template.txt`` and ``reflex_main.py``) over
    the default app code.

    :param overlay_folder: folder holding the env specific app code files
    :param dest_folder: the app code folder where the overlay is applied
    """
    if os.path.isdir(overlay_folder):
        shutil.copytree(overlay_folder, dest_folder, dirs_exist_ok=True)


def build_env_template_vars(app_type: str, env_type: str, snake_case_name: str) -> dict[str, str]:
    """Build the template variables that inject a virtual environment in the generate task.

    When ``env_type`` is "NONE" the env related placeholders are replaced by empty strings,
    producing the same generate task as before.

    :param app_type: "streamlit" or "reflex"
    :param env_type: "NONE", "PIP", "CONDA" or "MAMBA"
    :param snake_case_name: the snake_case name of the app
    :return: dictionary of template variables to replace in the generate task file
    """
    if env_type == "NONE":
        return {"envImport": "", "getShellProxy": ""}

    proxy_class, proxy_module = ENV_SHELL_PROXY[env_type]
    env_file_name = get_env_file_name(app_type, env_type)
    env_name = StringHelper.to_pascal_case(snake_case_name) + "Env"

    env_import = (
        f"from {proxy_module} import {proxy_class}\n"
        "from gws_core.impl.shell.shell_proxy import ShellProxy\n"
    )

    get_shell_proxy = (
        "\n"
        "    def get_shell_proxy(self) -> ShellProxy:\n"
        f"        # run the app in a {env_type.lower()} virtual environment described by the env file\n"
        f'        env_file_path = os.path.join(self.get_app_folder_path(), "{env_file_name}")\n'
        f'        return {proxy_class}(env_file_path=env_file_path, env_name="{env_name}")\n'
    )

    return {"envImport": env_import, "getShellProxy": get_shell_proxy}
