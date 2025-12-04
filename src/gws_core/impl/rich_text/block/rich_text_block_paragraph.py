from typing import Any, Literal, Optional

from bs4 import BeautifulSoup

from gws_core.core.model.model_dto import BaseModelDTO
from gws_core.impl.rich_text.block.rich_text_block import RichTextBlockDataBase, RichTextBlockType


class RichTextVariableData(BaseModelDTO):
    """Object representing a variable in a rich text"""

    name: str
    description: Optional[str] = None
    value: Optional[Any] = None
    type: Literal["string"]

    def to_markdown(self) -> str:
        """Convert the variable to markdown

        :return: the markdown representation of the variable
        :rtype: str
        """
        return f"${{{self.name}}}"


class ReplaceWithBlockResultDTO(BaseModelDTO):
    before: str
    after: str
    variable_data: RichTextVariableData


class RichTextBlockParagraph(RichTextBlockDataBase):
    """Class to manipulate the rich text paragraph text (including variables)"""

    # Instance attribute
    text: str

    def replace_parameter_with_text(
        self, parameter_name: str, value: str, replace_block: bool = False
    ) -> None:
        """Replace the variable in the rich text content text

        :param variable_name: the name of the variable to replace
        :type variable_name: str
        :param value: the value to replace the variable
        :type value: str
        :param replace_block: if True, the variable block will be remove and only the value will be displayed
        :type replace_block: bool
        :return: the updated text if the variable was found and replaced
        :rtype: str
        """
        variable_applied = False
        soup: BeautifulSoup
        if self.get_variable_tag_name() in self.text:
            soup = BeautifulSoup(self.text, "html.parser")
            for tag in soup.find_all(self.get_variable_tag_name()):
                if self.get_variable_json_attribute() not in tag.attrs:
                    continue
                # read the json data attribute and convert it to a dict
                json_data = tag[self.get_variable_json_attribute()]
                variable_data: RichTextVariableData = RichTextVariableData.from_json_str(json_data)

                if variable_data.name.strip() == parameter_name.strip():
                    variable_data.value = value

                    # if replace is set to True, we remove the block and only display the value
                    # using beautifulsoup
                    if replace_block:
                        tag.replace_with(value)
                    else:
                        # update the json data attribute
                        tag[self.get_variable_json_attribute()] = variable_data.to_json_str()
                    variable_applied = True

        if variable_applied:
            self.text = str(soup)

    def replace_parameter_with_block(self, variable_name: str) -> ReplaceWithBlockResultDTO:
        """Replace the variable in the rich text content text

        :param variable_name: the name of the variable to replace
        :type variable_name: str
        :param value: the value to replace the variable
        :type value: str
        :return: the updated text if the variable was found and replaced
        :rtype: str
        """
        soup: BeautifulSoup
        if self.get_variable_tag_name() in self.text:
            soup = BeautifulSoup(self.text, "html.parser")
            for tag in soup.find_all(self.get_variable_tag_name()):
                if self.get_variable_json_attribute() not in tag.attrs:
                    continue
                # read the json data attribute and convert it to a dict
                json_data = tag[self.get_variable_json_attribute()]
                variable_data: RichTextVariableData = RichTextVariableData.from_json_str(json_data)

                if variable_data.name.strip() == variable_name.strip():
                    before = self.get_elements_before_as_str(tag)
                    after = self.get_elements_after_as_str(tag)

                    return ReplaceWithBlockResultDTO(
                        before=before, after=after, variable_data=variable_data
                    )

        return None

    def get_elements_before_as_str(self, target_element: BeautifulSoup) -> str:
        result: str = ""
        current_element = target_element.previous_sibling
        while current_element is not None:
            result = str(current_element) + result
            current_element = current_element.previous_sibling
        return result

    def get_elements_after_as_str(self, target_element: BeautifulSoup) -> str:
        result: str = ""
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

    def is_empty(self) -> bool:
        """Check if the paragraph is empty

        :return: True if the paragraph is empty, False otherwise
        :rtype: bool
        """
        return not self.text or len(self.text.strip()) == 0

    def to_markdown(self) -> str:
        """Convert the paragraph to markdown

        :return: the markdown representation of the paragraph
        :rtype: str
        """
        return self.text

    def get_type(self):
        return RichTextBlockType.PARAGRAPH

    @classmethod
    def get_variable_tag_name(cls) -> str:
        """Get the variable tag name

        :return: the variable tag name
        :rtype: str
        """
        return "te-variable-inline"

    @classmethod
    def get_variable_json_attribute(cls) -> str:
        """Get the variable json attribute

        :return: the variable json attribute
        :rtype: str
        """
        return "data-jsondata"
