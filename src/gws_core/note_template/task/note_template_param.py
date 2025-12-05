
from gws_core.config.param.model_param import ModelParam
from gws_core.config.param.param_spec_decorator import ParamSpecType, param_spec_decorator
from gws_core.config.param.param_types import ParamSpecDTO, ParamSpecTypeStr, ParamSpecVisibilty
from gws_core.core.model.model import Model
from gws_core.note_template.note_template import NoteTemplate


@param_spec_decorator(type_=ParamSpecType.LAB_SPECIFIC)
class NoteTemplateParam(ModelParam):
    """Note template params spec. When used, the end user will be able to select a note template
    from the list of note template available in the lab.

    The accessible value will be note template.

    """

    def __init__(
        self,
        optional: bool = False,
        visibility: ParamSpecVisibilty = "public",
        human_name: str | None = "Select note template",
        short_description: str | None = None,
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
        return ParamSpecTypeStr.NOTE_TEMPLATE

    def get_model_type(self) -> type[Model]:
        """Override this method to return the model type to use

        :return: The model type
        :rtype: Type[Model]
        """
        return NoteTemplate

    @classmethod
    def get_default_value_param_spec(cls) -> "NoteTemplateParam":
        return NoteTemplateParam()

    @classmethod
    def get_additional_infos(cls) -> dict[str, ParamSpecDTO]:
        return None
