
import os

import typer

from gws_core import FileHelper, StringHelper

NAME_VAR = 'name'
HUMAN_NAME_VAR = 'humanName'
SHORT_DESCRIPTION_VAR = 'shortDescription'

TEMPLATE_PATH = os.path.join(os.path.dirname(__file__), 'task_template.txt')


def create_task(name: str, human_name: str = '', short_description: str = '') -> str:
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

    task_file = os.path.join(os.getcwd(), f'{StringHelper.to_snake_case(name)}.py')

    if FileHelper.exists_on_os(task_file):
        typer.echo(f"File '{task_file}' already exists.", err=True)
        raise typer.Abort()

    task_code: str = ''
    with open(TEMPLATE_PATH, 'r', encoding='UTF-8') as f:
        task_code = f.read()

    task_code = replace_variables(task_code, NAME_VAR, name)
    task_code = replace_variables(task_code, HUMAN_NAME_VAR, f', "{human_name}"' if human_name else name)
    task_code = replace_variables(task_code, SHORT_DESCRIPTION_VAR,
                                  f', "{short_description}"' if short_description else '')

    with open(task_file, 'w', encoding='UTF-8') as f:
        f.write(task_code)

    return task_file


def replace_variables(text: str, var_name: str, value: str) -> str:
    # variable are formatted as {{var_name}}
    text = text.replace('{{' + var_name + '}}', value)
    return text
