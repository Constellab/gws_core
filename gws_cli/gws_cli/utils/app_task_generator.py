
import os
import shutil
from typing import Literal

from gws_cli.utils.cli_utils import CLIUtils
from gws_core import StringHelper

NAME_VAR = 'name'
DASHBOARD_CLASS_VAR = 'appClass'
GENERATE_CLASS_VAR = 'generateClass'
FOLDER_APP_NAME_VAR = 'folderAppName'
APP_TYPE_RESOURCE = 'appTypeResource'
APP_TYPE_VAR = 'appTypeVar'
APP_TYPE = 'appType'


TEMPLATE_FOLDER = os.path.join(os.path.dirname(__file__), '_template')
TEMPLATE_APP_FOLDER_NAME = '_template_app'
TEMPLATE_GENERATE_APP_NAME = 'generate_app_template.txt'


def generate_app_task(snake_case_name: str, app_folder_path: str,
                      app_type: Literal['streamlit', 'reflex']) -> None:
    """ Method to create a new streamlit app with the given name.

    :param name: _description_
    :type name: str
    :raises ValueError: _description_
    :return: path to the created streamlit app
    :rtype: str
    """
    # Rename the generate task
    generate_app_old_path = os.path.join(TEMPLATE_FOLDER, TEMPLATE_GENERATE_APP_NAME)
    generate_app_new_path = os.path.join(app_folder_path, f"generate_{snake_case_name}.py")
    shutil.copy2(generate_app_old_path, generate_app_new_path)

    app_pascal_name = StringHelper.to_pascal_case(snake_case_name)

    # Replace the variables in the generate task
    replace_variables = {
        NAME_VAR: app_pascal_name,
        DASHBOARD_CLASS_VAR: f"{app_pascal_name}Dashboard",
        GENERATE_CLASS_VAR: f"Generate{app_pascal_name}",
        FOLDER_APP_NAME_VAR: '_' + snake_case_name,
        APP_TYPE_RESOURCE: app_type.capitalize() + 'Resource',
        APP_TYPE_VAR: app_type + '_app',
        APP_TYPE: app_type.upper()
    }
    CLIUtils.replace_vars_in_file(generate_app_new_path, replace_variables)
