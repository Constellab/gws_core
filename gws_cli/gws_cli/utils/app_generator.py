import os
import shutil
from typing import Literal

import typer
from gws_core import FileHelper, StringHelper

from gws_cli.utils.cli_utils import CLIUtils

NAME_VAR = "name"
DASHBOARD_CLASS_VAR = "appClass"
GENERATE_CLASS_VAR = "generateClass"
FOLDER_APP_NAME_VAR = "folderAppName"
APP_TYPE_RESOURCE = "appTypeResource"
APP_TYPE_VAR = "appTypeVar"
APP_TYPE = "appType"


TEMPLATE_FOLDER = os.path.join(os.path.dirname(__file__), "_template")
TEMPLATE_APP_FOLDER_NAME = "_template_app"
TEMPLATE_GENERATE_APP_NAME = "generate_app_template.txt"


class AppGenerator:
    """Class to handle app generation tasks with common functionality."""

    @classmethod
    def validate_app_name_and_folder(cls, name: str, folder: str) -> str:
        """Validate app name and check if folder already exists.

        :param name: The name of the app
        :type name: str
        :param folder: The folder where the app will be created
        :type folder: str
        :raises typer.Abort: If validation fails
        :return: The snake_case version of the app name
        :rtype: str
        """
        if not StringHelper.is_alphanumeric(name):
            typer.echo(
                f"Invalid app name '{name}'. It must contains only alpha numeric characters and '_'.",
                err=True,
            )
            raise typer.Abort()

        snake_case_name = StringHelper.to_snake_case(name)

        # The folder where the app will be created
        app_folder = os.path.join(os.getcwd(), snake_case_name)

        if FileHelper.exists_on_os(app_folder):
            typer.echo(f"Folder '{app_folder}' already exists.", err=True)
            raise typer.Abort()

        # Check if we are in a brick src folder
        brick_name = CLIUtils.check_folder_is_in_brick_src(folder)

        # Check if the app name is different than the brick name
        if snake_case_name == brick_name:
            typer.echo(
                f"The app name '{snake_case_name}' cannot be the same as the brick name '{brick_name}'.",
                err=True,
            )
            raise typer.Abort()

        return snake_case_name

    @classmethod
    def generate_app_task(
        cls, snake_case_name: str, app_folder_path: str, app_type: Literal["streamlit", "reflex"]
    ) -> None:
        """Method to create the generate app task file.

        :param snake_case_name: The snake_case name of the app
        :type snake_case_name: str
        :param app_folder_path: The path to the app folder
        :type app_folder_path: str
        :param app_type: The type of app (streamlit or reflex)
        :type app_type: Literal["streamlit", "reflex"]
        """
        # Rename the generate task
        generate_app_old_path = os.path.join(TEMPLATE_FOLDER, TEMPLATE_GENERATE_APP_NAME)
        generate_app_new_path = os.path.join(app_folder_path, f"generate_{snake_case_name}.py")
        shutil.copy2(generate_app_old_path, generate_app_new_path)

        cls.replace_vars_in_file(snake_case_name, generate_app_new_path, app_type)

    @classmethod
    def replace_vars_in_file(
        cls, snake_case_name: str, file_path: str, app_type: Literal["streamlit", "reflex"]
    ) -> None:
        """Method to replace variables in app file.

        :param snake_case_name: The snake_case name of the app
        :type snake_case_name: str
        :param file_path: The path to the file to replace variables in
        :type file_path: str
        :param app_type: The type of app (streamlit or reflex)
        :type app_type: Literal["streamlit", "reflex"]
        """
        # Rename the generate task
        app_pascal_name = StringHelper.to_pascal_case(snake_case_name)

        # Replace the variables in the generate task
        replace_variables = {
            NAME_VAR: app_pascal_name,
            DASHBOARD_CLASS_VAR: f"{app_pascal_name}AppConfig",
            GENERATE_CLASS_VAR: f"Generate{app_pascal_name}",
            FOLDER_APP_NAME_VAR: "_" + snake_case_name,
            APP_TYPE_RESOURCE: app_type.capitalize() + "Resource",
            APP_TYPE_VAR: app_type + "_app",
            APP_TYPE: app_type.upper(),
        }
        CLIUtils.replace_vars_in_file(file_path, replace_variables)
