
from typing import Any, Dict, Optional

from gws_core.config.param.param_spec import ParamSpec
from gws_core.config.param.param_spec_decorator import (ParamaSpecType,
                                                        param_spec_decorator)
from gws_core.config.param.param_types import (ParamSpecDTO, ParamSpecTypeStr,
                                               ParamSpecVisibilty)
from gws_core.core.classes.validator import StrValidator
from gws_core.folder.space_folder import SpaceFolder


@param_spec_decorator(type_=ParamaSpecType.LAB_SPECIFIC)
class SpaceFolderParam(ParamSpec):
    """ Space folder param spec. When used, the end user will be able to select a space folder from
    the list of available space folders. The config stores only the space folder id, not the full space folder object.

    The accessible value in task is a Space folder.
    See the documentation of the credentials type for more info.

    """

    def __init__(self,
                 optional: bool = False,
                 visibility: ParamSpecVisibilty = "public",
                 human_name: Optional[str] = 'Select a folder',
                 short_description: Optional[str] = None,
                 ):
        """
        :param optional: See default value
        :type optional: Optional[str]
        :param visibility: Visibility of the param, see doc on type ParamSpecVisibilty for more info
        :type visibility: ParamSpecVisibilty
        :param human_name: Human readable name of the param, showed in the interface
        :type human_name: Optional[str]
        :param short_description: Description of the param, showed in the interface
        :type short_description: Optional[str]
        """

        super().__init__(
            optional=optional,
            visibility=visibility,
            human_name=human_name,
            short_description=short_description,
        )

    @classmethod
    def get_str_type(cls) -> ParamSpecTypeStr:
        return ParamSpecTypeStr.SPACE_FOLDER

    def build(self, value: Any) -> SpaceFolder:
        if not value:
            return None

        return SpaceFolder.get_by_id_and_check(value)

    def validate(self, value: Any) -> str:

        if isinstance(value, SpaceFolder):
            return value.id
        # if this is the credentials object, retrieve the name
        if isinstance(value, dict) and 'id' in value:
            value = value['id']

        validator = StrValidator()
        return validator.validate(value)

    @classmethod
    def get_default_value_param_spec(cls) -> "SpaceFolderParam":
        return SpaceFolderParam()

    @classmethod
    def get_additional_infos(cls) -> Dict[str, ParamSpecDTO]:
        return None
