

import json

from bs4 import BeautifulSoup

from gws_core.core.model.model_dto import BaseModelDTO
from gws_core.impl.rich_text.rich_text_types import RichTextVariableData


class ReplaceWithBlockResultDTO(BaseModelDTO):
    before: str
    after: str
    variable_data: dict


class RichTextParagraphText():
    """Class to manipulate the rich text paragraph text (including variables)
    """

    text: str = None

    VARIABLE_TAG_NAME = 'te-variable-inline'
    VARIABLE_JSON_ATTRIBUTE = 'data-jsondata'

    def __init__(self, text: str):
        self.text = text

    def replace_variable_with_text(self, variable_name: str, value: str) -> str:
        """Replace the variable in the rich text content text

        :param variable_name: the name of the variable to replace
        :type variable_name: str
        :param value: the value to replace the variable
        :type value: str
        :return: the updated text if the variable was found and replaced
        :rtype: str
        """
        variable_applied = False
        soup: BeautifulSoup
        if self.VARIABLE_TAG_NAME in self.text:
            soup = BeautifulSoup(self.text, 'html.parser')
            for tag in soup.find_all(self.VARIABLE_TAG_NAME):
                if self.VARIABLE_JSON_ATTRIBUTE not in tag.attrs:
                    continue
                # read the json data attribute and convert it to a dict
                json_data = tag[self.VARIABLE_JSON_ATTRIBUTE]
                variable_data: RichTextVariableData = json.loads(json_data)

                if variable_data.get('name') == variable_name:
                    variable_data['value'] = value

                    # update the json data attribute
                    tag[self.VARIABLE_JSON_ATTRIBUTE] = json.dumps(variable_data)
                    variable_applied = True

        if variable_applied:
            return str(soup)

        return None

    def replace_variable_with_block(self, variable_name: str) -> ReplaceWithBlockResultDTO:
        """Replace the variable in the rich text content text

        :param variable_name: the name of the variable to replace
        :type variable_name: str
        :param value: the value to replace the variable
        :type value: str
        :return: the updated text if the variable was found and replaced
        :rtype: str
        """
        soup: BeautifulSoup
        if self.VARIABLE_TAG_NAME in self.text:
            soup = BeautifulSoup(self.text, 'html.parser')
            for tag in soup.find_all(self.VARIABLE_TAG_NAME):
                if self.VARIABLE_JSON_ATTRIBUTE not in tag.attrs:
                    continue
                # read the json data attribute and convert it to a dict
                json_data = tag[self.VARIABLE_JSON_ATTRIBUTE]
                variable_data: RichTextVariableData = json.loads(json_data)

                if variable_data.get('name').strip() == variable_name.strip():

                    before = self.get_elements_before_as_str(tag)
                    after = self.get_elements_after_as_str(tag)

                    return ReplaceWithBlockResultDTO(before=before, after=after, variable_data=variable_data)

        return None

    def get_elements_before_as_str(self, target_element: BeautifulSoup) -> str:
        result: str = ''
        current_element = target_element.previous_sibling
        while current_element is not None:
            result = str(current_element) + result
            current_element = current_element.previous_sibling
        return result

    def get_elements_after_as_str(self, target_element: BeautifulSoup) -> str:
        result: str = ''
        current_element = target_element.next_sibling
        while current_element is not None:
            result = result + str(current_element)
            current_element = current_element.next_sibling
        return result

    # def extract_variable(self, html_string, var_name, var_value) -> SearchVariableResultDTO:
    #     soup = BeautifulSoup(html_string, 'html.parser')
    #     variable_tags = soup.find_all('te-variable-inline')
    #     for tag in variable_tags:
    #         json_data = json.loads(tag['data-jsondata'])
    #         if json_data.get('name') == var_name:
    #             # Create a new element with the variable value
    #             new_content = soup.new_string(var_value)
    #             # Replace the variable tag with the new content
    #             tag.replace_with(new_content)
    #             # Get the modified HTML as a string
    #             modified_html = str(soup)
    #             # Split the modified HTML based on the new content
    #             before, after = modified_html.split(var_value, 1)
    #             return SearchVariableResultDTO(before=before, variable=json_data, after=after)
    #     return None
