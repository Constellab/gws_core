
from abc import abstractmethod
from typing import Any, Optional, Type

from gws_core.config.param.param_spec import ParamSpec
from gws_core.config.param.param_types import ParamSpecVisibilty
from gws_core.core.classes.validator import StrValidator
from gws_core.core.model.model import Model


class ModelParam(ParamSpec[str]):
    """ Abstract param spec to select an model from the DB and return it in the task
    """

    def __init__(self,
                 optional: bool = False,
                 visibility: ParamSpecVisibilty = "public",
                 human_name: Optional[str] = "Select object",
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

    @abstractmethod
    def get_model_type(self) -> Type[Model]:
        """Override this method to return the model type to use

        :return: The model type
        :rtype: Type[Model]
        """

    def build(self, value: Any) -> Optional[Model]:
        model_type = self.get_model_type()
        model: Optional[Model] = None
        if value and isinstance(value, str):

            # retrieve the document template and return it
            model = model_type.get_by_id(value)
            if model is None:
                raise Exception(f"Object '{model_type.classname()}' with id '{value}' not found")

        return model

    def validate(self, value: Any) -> str:
        model_type = self.get_model_type()
        if isinstance(value, model_type):
            return value.id
        # if this is the credentials object, retrieve the name
        if isinstance(value, dict) and 'id' in value:
            value = value['id']

        validator = StrValidator()
        return validator.validate(value)
