
import os
import shutil

import typer

from gws_cli.utils.cli_utils import CLIUtils
from gws_core import FileHelper, StringHelper

NAME_VAR = 'name'
HUMAN_NAME_VAR = 'humanName'
SHORT_DESCRIPTION_VAR = 'shortDescription'

TEMPLATE_PATH = os.path.join(os.path.dirname(__file__), 'task_template.txt')


def generate_task(name: str, human_name: str = '', short_description: str = '') -> str:
    """ Method to create a new task file with the given name, human name and short description.

    :param name: _description_
    :type name: str
    :param human_name: _description_, defaults to ''
    :type human_name: str, optional
    :param short_description: _description_, defaults to ''
    :type short_description: str, optional
    :raises ValueError: _description_
    :return: path to the created task file
    :rtype: str
    """

    if not StringHelper.is_alphanumeric(name):
        typer.echo(f"Invalid task name '{name}'. It must contains only alpha numeric characters and '_'.", err=True)
        raise typer.Abort()

    task_file_path = os.path.join(os.getcwd(), f'{StringHelper.to_snake_case(name)}.py')

    if FileHelper.exists_on_os(task_file_path):
        typer.echo(f"File '{task_file_path}' already exists.", err=True)
        raise typer.Abort()

    # copy the template file to the new task file
    shutil.copy(TEMPLATE_PATH, task_file_path)

    try:

        replace_variables = {
            NAME_VAR: name
        }

        human_name = human_name if human_name else name
        if human_name:
            replace_variables[HUMAN_NAME_VAR] = f', human_name="{human_name}"'
        else:
            replace_variables[HUMAN_NAME_VAR] = ''

        if short_description:
            replace_variables[SHORT_DESCRIPTION_VAR] = f', short_description="{short_description}"'
        else:
            replace_variables[SHORT_DESCRIPTION_VAR] = ''

        CLIUtils.replace_vars_in_file(task_file_path, replace_variables)

        return task_file_path

    except Exception as e:
        os.remove(task_file_path)
        raise e
