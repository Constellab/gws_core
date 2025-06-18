import os
import shutil

import typer

from gws_cli.utils.app_task_generator import generate_app_task
from gws_cli.utils.cli_utils import CLIUtils
from gws_cli.utils.typer_message_observer import TyperMessageObserver
from gws_core import FileHelper, ShellProxy, StringHelper

APP_NAME_VAR = 'APP_NAME'

TEMPLATE_FOLDER = os.path.join(os.path.dirname(__file__), '_template')
DEV_CONFIG_FILE = 'dev_config.json'
REFLEX_MAIN_FILE = 'reflex_main.py'


def generate_reflex_app(name: str) -> str:
    """ Method to create a new reflex app with the given name.

    :param name: _description_
    :type name: str
    :raises ValueError: _description_
    :return: path to the created reflex app
    :rtype: str
    """
    if not StringHelper.is_alphanumeric(name):
        typer.echo(
            f"Invalid reflex app name '{name}'. It must contains only alpha numeric characters and '_'.", err=True)
        raise typer.Abort()

    snake_case_name = StringHelper.to_snake_case(name)

    # The folder where the app will be created
    app_folder = os.path.join(os.getcwd(), snake_case_name)

    if FileHelper.exists_on_os(app_folder):
        typer.echo(f"Folder '{app_folder}' already exists.", err=True)
        raise typer.Abort()

    # create the app folder
    FileHelper.create_dir_if_not_exist(app_folder)

    reflex_app_folder = os.path.join(app_folder, '_' + snake_case_name)
    FileHelper.create_dir_if_not_exist(reflex_app_folder)

    try:
        # Run the reflex init command to generate the base app
        typer.echo(f"Generating Reflex app '{name}'...")
        shell = ShellProxy(working_dir=reflex_app_folder)
        shell.attach_observer(TyperMessageObserver())
        result = shell.run(
            ["reflex", "init", "--name", snake_case_name, '--template', 'blank'],
            dispatch_stdout=True, dispatch_stderr=True)

        if result != 0:
            typer.echo(
                f"Failed to generate Reflex app. Command 'reflex init --name {snake_case_name}' returned {result}",
                err=True)
            raise typer.Abort()

        # Replace the rxconfig.py file with our template
        template_rxconfig_path = os.path.join(TEMPLATE_FOLDER, "rxconfig.py")
        app_rxconfig_path = os.path.join(reflex_app_folder, "rxconfig.py")

        if not FileHelper.exists_on_os(app_rxconfig_path):
            typer.echo(f"Expected rxconfig.py not found at '{app_rxconfig_path}'", err=True)
            raise typer.Abort()
        # Replace the rxconfig.py with our template

        shutil.copy2(template_rxconfig_path, app_rxconfig_path)

        # Replace the APP_NAME variable in rxconfig.py
        replace_variables = {
            APP_NAME_VAR: snake_case_name
        }
        CLIUtils.replace_vars_in_file(app_rxconfig_path, replace_variables)

        # Copy the dev_config.json file
        dev_config_path = os.path.join(TEMPLATE_FOLDER, DEV_CONFIG_FILE)
        app_dev_config_path = os.path.join(reflex_app_folder, DEV_CONFIG_FILE)
        if not FileHelper.exists_on_os(dev_config_path):
            typer.echo(f"Expected dev_config.json not found at '{dev_config_path}'", err=True)
            raise typer.Abort()
        shutil.copy2(dev_config_path, app_dev_config_path)

        # Copy the reflex_main.py file, override the default one
        reflex_main_template_path = os.path.join(TEMPLATE_FOLDER, REFLEX_MAIN_FILE)
        app_reflex_main_path = os.path.join(reflex_app_folder, snake_case_name, snake_case_name + '.py')
        shutil.copy2(reflex_main_template_path, app_reflex_main_path)

        # Create the generate task file
        generate_app_task(snake_case_name, app_folder, 'reflex')

        typer.echo(f"Successfully created Reflex app at '{reflex_app_folder}'")
        return reflex_app_folder

    except Exception as e:
        # Clean up if something went wrong
        if FileHelper.exists_on_os(app_folder):
            shutil.rmtree(app_folder)
        typer.echo(f"Error generating Reflex app: {str(e)}", err=True)
        raise e
