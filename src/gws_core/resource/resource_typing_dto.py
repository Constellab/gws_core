

from typing import Dict, List, Optional

from gws_core.core.model.model_dto import BaseModelDTO
from gws_core.core.utils.reflector_types import MethodDoc
from gws_core.model.typing_dto import TypingFullDTO
from gws_core.resource.view.view_dto import ResourceViewMetadatalDTO


class ResourceTypingMethodDTO(BaseModelDTO):
    funcs: Optional[List[MethodDoc]]
    views: Optional[List[ResourceViewMetadatalDTO]]

    def to_markdown(self, resource_class_name: str) -> str:
        markdown = ""

        markdown += '\n\n### Methods\n'
        if self.funcs:
            for func in self.funcs:
                markdown += func.to_markdown(resource_class_name) + "\n"
        else:
            markdown += 'No method.'

        markdown += '\n\n### Views\n'
        if self.views:
            for view in self.views:
                markdown += view.to_markdown(resource_class_name) + "\n"
        else:
            markdown += 'No view.'
        return markdown


class ResourceTypingVariableDTO(BaseModelDTO):
    name: str
    type: str
    doc: str


class ResourceTypingDTO(TypingFullDTO):
    variables: Optional[Dict[str, str]]
    methods: Optional[ResourceTypingMethodDTO]

    def to_markdown(self) -> str:
        markdown = super().to_markdown()

        if self.variables:
            markdown += '\n\n**Attributes:**\n'
            for key, value in self.variables.items():
                markdown += f"- {key} : `{value}`\n"
        else:
            markdown += '\n\nNo attribute.'

        markdown += self.methods.to_markdown(self.human_name)

        return markdown
