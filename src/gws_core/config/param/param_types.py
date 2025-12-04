from enum import Enum
from typing import Any, Dict, List, Literal, Optional, Type

from gws_core.core.model.model_dto import BaseModelDTO

ParamValue = Any
ParamValueType = Type[ParamValue]


# Visibility of a param
# Public --> main param visible in the first config section in the interface
# Protected --> considered as advanced param, it will be in the advanced section in the interface (it must have a default value or be optional)
# Private --> private param, it will not be visible in the interface (it must have a default value or be optional)
ParamSpecVisibilty = Literal["public", "protected", "private"]


class ParamSpecTypeStr(Enum):
    STRING = "str"
    TEXT = "text"
    BOOL = "bool"
    INT = "int"
    FLOAT = "float"
    DICT = "dict"
    LIST = "list"
    DYNAMIC_PARAM = "dynamic"
    PARAM_SET = "param_set"
    TAGS = "tags_param"
    BASH_CODE = "bash_code_param"
    JSON_CODE = "json_code_param"
    JULIA_CODE = "julia_code_param"
    PERL_CODE = "perl_code_param"
    PYTHON_CODE = "python_code_param"
    R_CODE = "r_code_param"
    YAML_CODE = "yaml_code_param"
    CREDENTIALS = "credentials_param"
    SPACE_FOLDER = "space_folder_param"
    OPEN_AI_CHAT = "open_ai_chat_param"
    RICH_TEXT = "rich_text_param"
    NOTE = "note_param"
    NOTE_TEMPLATE = "note_template_param"
    SCENARIO = "scenario_param"


class ParamSpecSimpleDTO(BaseModelDTO):
    type: ParamSpecTypeStr
    optional: bool
    visibility: Optional[ParamSpecVisibilty] = "public"
    default_value: Optional[ParamValue] = None
    additional_info: Optional[Dict] = {}


class ParamSpecDTO(ParamSpecSimpleDTO):
    human_name: Optional[str] = None
    short_description: Optional[str] = None

    def to_markdown(self) -> str:
        markdown = f"- {self.human_name} (`{self.type}`"
        if self.optional:
            markdown += ", optional"

        markdown += ")"

        markdown += f": {self.short_description}"

        # write the default value (only for basic types)
        basic_types = [
            ParamSpecTypeStr.STRING,
            ParamSpecTypeStr.TEXT,
            ParamSpecTypeStr.BOOL,
            ParamSpecTypeStr.INT,
            ParamSpecTypeStr.FLOAT,
        ]
        if self.type in [basic_types] and self.default_value:
            markdown += f", default to '{self.default_value}'"

        return markdown


class ParamSpecInfoSpecs(BaseModelDTO):
    optional: ParamSpecDTO
    # visibility: ParamSpecDTO
    name: ParamSpecDTO
    short_description: ParamSpecDTO
    human_name: Optional[ParamSpecDTO] = None
    default_value: Optional[ParamSpecDTO] = None
    additional_info: Optional[Dict[str, ParamSpecDTO]] = None


DynamicParamAllowedSpecsDict = Dict[str, ParamSpecInfoSpecs]

CompleteDynamicParamAllowedSpecsDict = Dict[str, DynamicParamAllowedSpecsDict]
