from typing import Dict, Optional, Type

from gws_core.config.param.model_param import ModelParam
from gws_core.config.param.param_spec_decorator import ParamSpecType, param_spec_decorator
from gws_core.config.param.param_types import ParamSpecDTO, ParamSpecTypeStr, ParamSpecVisibilty
from gws_core.core.model.model import Model
from gws_core.note.note import Note


@param_spec_decorator(type_=ParamSpecType.LAB_SPECIFIC)
class NoteParam(ModelParam):
    """Note params spec. When used, the end user will be able to select a note
    from the list of note available in the lab.

    The accessible value will be NoteResource.

    """

    def __init__(
        self,
        optional: bool = False,
        visibility: ParamSpecVisibilty = "public",
        human_name: Optional[str] = "Select note",
        short_description: Optional[str] = None,
    ):
        """
        :param optional: See default value
        :type optional: Optional[str]
        :param visibility: Visibility of the param, see doc on type ParamSpecVisibilty for more info
        :type visibility: ParamSpecVisibilty
        :type default: Optional[ConfigParamType]
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
        return ParamSpecTypeStr.NOTE

    def get_model_type(self) -> Type[Model]:
        """Override this method to return the model type to use

        :return: The model type
        :rtype: Type[Model]
        """
        return Note

    @classmethod
    def get_default_value_param_spec(cls) -> "NoteParam":
        return NoteParam()

    @classmethod
    def get_additional_infos(cls) -> Dict[str, ParamSpecDTO]:
        return None
