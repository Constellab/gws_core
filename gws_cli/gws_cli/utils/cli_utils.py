

from typing import Dict


class CLIUtils:

    @staticmethod
    def replace_vars_in_file(file_path: str, variables: Dict[str, str]):
        """Method to replace the variables in a file.
        The variables are formatted as {{var_name}} in the file.

        :param file_path: path to the file
        :type file_path: str
        :param vars: dictionary of variables to replace
        :type vars: Dict[str, str]
        """
        with open(file_path, 'r', encoding='UTF-8') as f:
            text = f.read()

            for key, value in variables.items():
                text = CLIUtils.replace_variable(text, key, value)

        with open(file_path, 'w', encoding='UTF-8') as f:
            f.write(text)

    @staticmethod
    def replace_variable(text: str, var_name: str, value: str) -> str:
        # variable are formatted as {{var_name}}
        text = text.replace('{{' + var_name + '}}', value)
        return text
