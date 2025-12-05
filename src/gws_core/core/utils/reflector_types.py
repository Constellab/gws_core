
from docstring_parser import parse

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
    doc: str | None
    args: list[MethodArgDoc]
    return_type: str | None
    method_type: str | None

    def get_arg_description(self, arg_name: str) -> str | None:
        """Method to extract the description of an argument from the docstring of the method
        For this method it will extract 'argument_name' for argument 'arg_name'

        :param arg_name: argument name
        :type arg_name: str
        :return: _description_
        :rtype: Optional[str]
        """
        if not self.doc:
            return None

        try:
            parsed_doc = parse(self.doc)
            for param in parsed_doc.params:
                if param.arg_name == arg_name:
                    return param.description
        except Exception:
            # Fallback to None if parsing fails
            pass
        return None

    def get_return_description(self) -> str | None:
        """Method to extract the description of the return value from the docstring of the method
        For this method it will extract 'description of the return value'

        :return: description of the return value
        :rtype: Optional[str]
        """
        if not self.doc:
            return None

        try:
            parsed_doc = parse(self.doc)
            if parsed_doc.returns:
                return parsed_doc.returns.description
        except Exception:
            # Fallback to None if parsing fails
            pass
        return None

    def get_doc_without_args(self) -> str:
        """Method to extract the description of the method without the arguments nor the return value

        :return: description of the method
        :rtype: str
        """
        if not self.doc:
            return None

        try:
            parsed_doc = parse(self.doc)
            # Get short and long description, combining them
            short_desc = parsed_doc.short_description or ""
            long_desc = parsed_doc.long_description or ""

            if short_desc and long_desc:
                return f"{short_desc}\n\n{long_desc}"
            elif short_desc:
                return short_desc
            elif long_desc:
                return long_desc
        except Exception:
            # Fallback to returning the original doc if parsing fails
            pass
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
    doc: str | None
    methods: list[MethodDoc] | None
    variables: dict | None
