import re
from typing import Any, Dict, List, Optional

from gws_core.core.model.model_dto import BaseModelDTO


# enum
class MethodDocType(str):
    CLASSMETHOD = "classmethod"
    STATICMETHOD = "staticmethod"
    BASICMETHOD = None


class MethodArgDoc(BaseModelDTO):
    arg_name: str
    arg_type: str
    arg_default_value: str

    def to_markdown(self, arg_description: str) -> str:
        markdown = f"- {self.arg_name} (`{self.arg_type}`): {arg_description}"
        if self.arg_default_value:
            markdown += f" ,default to {self.arg_default_value}"

        return markdown


class MethodDoc(BaseModelDTO):
    name: str
    doc: Optional[str]
    args: List[MethodArgDoc]
    return_type: Optional[str]
    method_type: Optional[str]

    def get_arg_description(self, arg_name: str) -> Optional[str]:
        """Method to extract the description of an argument from the docstring of the method
        For this method it will extract 'argument_name' for argument 'arg_name'

        :param arg_name: argument name
        :type arg_name: str
        :return: _description_
        :rtype: Optional[str]
        """
        if not self.doc:
            return None

        pattern = re.compile(rf":param {arg_name}: (.+?)(?=, defaults to|\n\s*:\w|\Z)", re.DOTALL)
        match = pattern.search(self.doc)
        if match:
            return match.group(1).strip()
        return None

    def get_return_description(self) -> Optional[str]:
        """Method to extract the description of the return value from the docstring of the method
        For this method it will extract 'description of the return value'

        :return: description of the return value
        :rtype: Optional[str]
        """
        if not self.doc:
            return None

        pattern = re.compile(r":return: (.+?)(?=\n\s*:\w|\Z)", re.DOTALL)
        match = pattern.search(self.doc)
        if match:
            return match.group(1).strip()
        return None

    def get_doc_without_args(self) -> str:
        """Method to extract the description of the method without the arguments nor the return value

        :return: description of the method
        :rtype: str
        """
        if not self.doc:
            return None

        pattern = re.compile(r"(.*?)(?=\n\s*:(param|type|rtype|return)|\Z)", re.DOTALL)
        match = pattern.search(self.doc)
        if match:
            return match.group(1).strip()
        return self.doc

    def to_markdown(self, class_name: str) -> str:
        markdown = f"#### {self.name} ({class_name})"

        if self.method_type:
            markdown += f" ({self.method_type})"

        markdown += "\n\n"

        doc_without_args = self.get_doc_without_args()
        if self.doc:
            markdown += f"{doc_without_args}\n\n"

        if len(self.args) > 0:
            markdown += "**Parameters:**\n"
            for arg in self.args:
                arg_description = self.get_arg_description(arg.arg_name)
                if arg_description is None:
                    arg_description = "No description provided."
                markdown += arg.to_markdown(arg_description) + "\n"
        else:
            markdown += "No parameters.\n"

        if self.return_type:
            markdown += f"\n**Returns** (`{self.return_type}`)"
            return_description = self.get_return_description()
            if return_description:
                markdown += f": {return_description}"

            markdown += "\n"

        return markdown


class ClassicClassDocDTO(BaseModelDTO):
    name: str
    doc: Optional[str]
    methods: Optional[List[MethodDoc]]
    variables: Optional[Dict]
