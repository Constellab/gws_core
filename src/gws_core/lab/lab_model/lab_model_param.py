from typing import Any

from gws_core.config.param.param_spec import ParamSpec
from gws_core.config.param.param_spec_decorator import ParamSpecCategory, param_spec_decorator
from gws_core.config.param.param_types import ParamSpecDTO, ParamSpecType, ParamSpecVisibilty
from gws_core.core.classes.validator import StrValidator
from gws_core.lab.lab_model.lab_dto import LabDTOWithCredentials
from gws_core.lab.lab_model.lab_model import LabModel


@param_spec_decorator(type_=ParamSpecCategory.LAB_SPECIFIC)
class LabModelParam(ParamSpec):
    """Lab model param spec. When used, the end user will be able to select a lab
    from the list of labs available in the system. The config stores only the lab model id.

    The accessible value in task is a LabDTOWithCredentials containing the lab info
    and its resolved credentials data.
    """

    def __init__(
        self,
        optional: bool = False,
        visibility: ParamSpecVisibilty = "public",
        human_name: str | None = None,
        short_description: str | None = None,
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
        if human_name is None:
            human_name = "Select lab"

        super().__init__(
            optional=optional,
            visibility=visibility,
            human_name=human_name,
            short_description=short_description,
        )

    @classmethod
    def get_param_spec_type(cls) -> ParamSpecType:
        return ParamSpecType.LAB_MODEL

    def build(self, value: Any) -> LabDTOWithCredentials | None:
        """Retrieve the LabModel by id and return its DTO with credentials."""
        if not value:
            return None

        lab: LabModel = LabModel.get_by_id_and_check(value)
        return lab.to_dto_with_credentials()

    def validate(self, value: Any) -> str:
        """Extract the id from LabModel, dict, or string."""
        if value is None:
            return value

        if isinstance(value, LabModel):
            return value.id

        if isinstance(value, dict) and "id" in value:
            value = value["id"]

        validator = StrValidator()
        return validator.validate(value)

    @classmethod
    def get_default_value_param_spec(cls) -> "LabModelParam":
        return LabModelParam()

    @classmethod
    def get_additional_infos(cls) -> dict[str, ParamSpecDTO] | None:
        return None
