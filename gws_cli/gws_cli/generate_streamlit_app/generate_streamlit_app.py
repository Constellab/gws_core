import os
import shutil

from gws_core import FileHelper

from gws_cli.utils.app_env_generator import (
    apply_env_app_overlay,
    build_env_template_vars,
    copy_env_file,
    validate_env_type,
)
from gws_cli.utils.app_generator import AppGenerator
from gws_cli.utils.cli_utils import CLIUtils
from gws_cli.utils.dev_config_generator import create_dev_config_json

TEMPLATE_FOLDER = os.path.join(os.path.dirname(__file__), "_template")
TEMPLATE_ENV_FOLDER = os.path.join(os.path.dirname(__file__), "_template_env")
# App code files specific to virtual environment apps, they override the default app code
TEMPLATE_ENV_APP_OVERLAY_FOLDER = os.path.join(TEMPLATE_ENV_FOLDER, "app_overlay")
GENERATE_APP_TEMPLATE_NAME = "generate_app_template.txt"
# The app entrypoint is shipped as a .txt file because it holds a "{{folderAppName}}"
# placeholder in an import statement, which is not valid python. It is renamed to
# main.py once copied in the generated app.
MAIN_TEMPLATE_NAME = "main_template.txt"


def _generate_streamlit_app_task(snake_case_name: str, app_folder: str, env_type: str) -> None:
    """Generate the ``generate_<name>.py`` task file from the streamlit generate template.

    :param snake_case_name: The snake_case name of the app
    :param app_folder: The path to the app folder where the task file is created
    :param env_type: Virtual environment type ("NONE", "PIP", "CONDA" or "MAMBA")
    """
    template_path = os.path.join(TEMPLATE_FOLDER, GENERATE_APP_TEMPLATE_NAME)
    generate_task_path = os.path.join(app_folder, f"generate_{snake_case_name}.py")
    shutil.copy2(template_path, generate_task_path)

    # Replace the common app variables (app class names, folder name, ...)
    AppGenerator.replace_vars_in_file(snake_case_name, generate_task_path, "streamlit")

    # Replace the env specific variables
    CLIUtils.replace_vars_in_file(
        generate_task_path,
        build_env_template_vars("streamlit", env_type, snake_case_name),
    )


def generate_streamlit_app(name: str, env_type: str = "NONE") -> str:
    """Method to create a new streamlit app with the given name.

    :param name: name of the streamlit app
    :type name: str
    :param env_type: virtual environment to run the app in. One of "NONE", "PIP",
        "CONDA" or "MAMBA". Defaults to "NONE".
    :type env_type: str
    :raises ValueError: if the env type is not supported
    :return: path to the created streamlit app
    :rtype: str
    """

    env_type = validate_env_type(env_type)

    # Validate app name and check if folder already exists
    current_folder = os.getcwd()
    snack_case_name = AppGenerator.validate_app_name_and_folder(name, current_folder)

    app_folder = os.path.join(current_folder, snack_case_name)

    FileHelper.create_dir_if_not_exist(app_folder)

    streamlit_app_folder = os.path.join(app_folder, "_" + snack_case_name)

    shutil.copytree(TEMPLATE_FOLDER, streamlit_app_folder, dirs_exist_ok=True)

    # The generate task template lives in the app code folder, move it out so it is not
    # shipped inside the streamlit app code.
    os.remove(os.path.join(streamlit_app_folder, GENERATE_APP_TEMPLATE_NAME))

    # Copy the env file inside the app code folder when a virtual env is requested
    dev_env_file_path = ""
    if env_type != "NONE":
        dev_env_file_path = copy_env_file(
            TEMPLATE_ENV_FOLDER, "streamlit", env_type, streamlit_app_folder
        )
        # A virtual env app cannot load gws_core, override the app code so it
        # imports from gws_streamlit_env_main instead.
        apply_env_app_overlay(TEMPLATE_ENV_APP_OVERLAY_FOLDER, streamlit_app_folder)

    # Generate dev_config.json using the common function
    create_dev_config_json(
        streamlit_app_folder,
        is_reflex_enterprise=False,
        is_streamlit_v2=True,
        env_type=env_type,
        env_file_path=dev_env_file_path,
    )

    # Rename the app entrypoint template to its final python file name
    main_destination = os.path.join(streamlit_app_folder, "main.py")
    os.rename(os.path.join(streamlit_app_folder, MAIN_TEMPLATE_NAME), main_destination)
    AppGenerator.replace_vars_in_file(snack_case_name, main_destination, "streamlit")

    try:
        # Create the generate task file, injecting the virtual env if requested
        _generate_streamlit_app_task(snack_case_name, app_folder, env_type)

        return streamlit_app_folder

    except Exception as e:
        shutil.rmtree(app_folder)
        raise e
