import os
import shutil

import typer
from gws_core import FileHelper, StringHelper

from gws_cli.utils.app_task_generator import generate_app_task, replace_vars_in_file
from gws_cli.utils.dev_config_generator import create_dev_config_json

TEMPLATE_FOLDER = os.path.join(os.path.dirname(__file__), "_template")


def generate_streamlit_app(name: str) -> str:
    """Method to create a new streamlit app with the given name.

    :param name: _description_
    :type name: str
    :raises ValueError: _description_
    :return: path to the created streamlit app
    :rtype: str
    """

    if not StringHelper.is_alphanumeric(name):
        typer.echo(
            f"Invalid streamlit app name '{name}'. It must contains only alpha numeric characters and '_'.",
            err=True,
        )
        raise typer.Abort()

    snack_case_name = StringHelper.to_snake_case(name)

    app_folder = os.path.join(os.getcwd(), snack_case_name)

    if FileHelper.exists_on_os(app_folder):
        typer.echo(f"Folder '{app_folder}' already exists.", err=True)
        raise typer.Abort()

    FileHelper.create_dir_if_not_exist(app_folder)

    streamlit_app_folder = os.path.join(app_folder, "_" + snack_case_name)

    shutil.copytree(TEMPLATE_FOLDER, streamlit_app_folder, dirs_exist_ok=True)

    # Generate dev_config.json using the common function
    create_dev_config_json(streamlit_app_folder, is_reflex_enterprise=False)

    main_destination = os.path.join(streamlit_app_folder, "main.py")
    replace_vars_in_file(snack_case_name, main_destination, "streamlit")

    try:
        # Rename the generate task
        # Create the generate task file
        generate_app_task(snack_case_name, app_folder, "streamlit")

        return streamlit_app_folder

    except Exception as e:
        shutil.rmtree(app_folder)
        raise e
