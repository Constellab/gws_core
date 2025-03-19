
import os
import shutil

import typer

from gws_cli.utils.cli_utils import CLIUtils
from gws_core import FileHelper, StringHelper

NAME_VAR = 'name'
DASHBOARD_CLASS_VAR = 'dashboardClass'
GENERATE_CLASS_VAR = 'generateClass'
FOLDER_APP_NAME_VAR = 'folderAppName'

TEMPLATE_FOLDER = os.path.join(os.path.dirname(__file__), '_template')
TEMPLATE_APP_FOLDER_NAME = '_template_app'
TEMPLATE_GENERATE_APP_NAME = 'generate_app_template.txt'


def generate_streamlit_app(name: str) -> str:
    """ Method to create a new streamlit app with the given name.

    :param name: _description_
    :type name: str
    :raises ValueError: _description_
    :return: path to the created streamlit app
    :rtype: str
    """

    if not StringHelper.is_alphanumeric(name):
        typer.echo(
            f"Invalid streamlit app name '{name}'. It must contains only alpha numeric characters and '_'.", err=True)
        raise typer.Abort()

    snack_case_name = StringHelper.to_snake_case(name)

    streamlit_app_folder = os.path.join(os.getcwd(), snack_case_name)

    if FileHelper.exists_on_os(streamlit_app_folder):
        typer.echo(f"Folder '{streamlit_app_folder}' already exists.", err=True)
        raise typer.Abort()

    shutil.copytree(
        TEMPLATE_FOLDER,
        streamlit_app_folder,
        dirs_exist_ok=True
    )

    try:

        folder_app_new_name = f"_{snack_case_name}"

        # Rename the generate task
        generate_app_old_path = os.path.join(streamlit_app_folder, TEMPLATE_GENERATE_APP_NAME)
        generate_app_new_path = os.path.join(streamlit_app_folder, f"generate_{snack_case_name}.py")
        os.rename(generate_app_old_path, generate_app_new_path)

        # Replace the variables in the generate task
        replace_variables = {
            NAME_VAR: name,
            DASHBOARD_CLASS_VAR: f"{name}Dashboard",
            GENERATE_CLASS_VAR: f"Generate{name}",
            FOLDER_APP_NAME_VAR: folder_app_new_name
        }
        CLIUtils.replace_vars_in_file(generate_app_new_path, replace_variables)

        # Rename the app folder
        app_folder_old_path = os.path.join(streamlit_app_folder, TEMPLATE_APP_FOLDER_NAME)
        app_folder_new_path = os.path.join(streamlit_app_folder, folder_app_new_name)
        os.rename(app_folder_old_path, app_folder_new_path)

        return streamlit_app_folder

    except Exception as e:
        shutil.rmtree(streamlit_app_folder)
        raise e
