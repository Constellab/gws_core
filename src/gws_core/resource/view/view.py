

from typing import Any, List, Optional, final

from gws_core.config.config_specs import ConfigSpecs
from gws_core.core.exception.exceptions.bad_request_exception import \
    BadRequestException
from gws_core.core.utils.string_helper import StringHelper
from gws_core.model.typing_style import TypingStyle
from gws_core.resource.technical_info import TechnicalInfo, TechnicalInfoDict
from gws_core.resource.view.view_dto import ViewDTO

from ...config.config_params import ConfigParams
from .view_types import ViewType


class View:

    _type: ViewType = ViewType.VIEW
    _title: Optional[str] = None
    _technical_info: TechnicalInfoDict
    _style: TypingStyle = None

    _disable_pagination: bool = False

    # if True, the view is marked as favorite
    _favorite: bool = False

    # Spec of the view. All the view spec must be optional or have a default value
    _specs: ConfigSpecs = ConfigSpecs({})

    def __init__(self):
        # Check view type
        if not isinstance(self._type, ViewType):
            raise BadRequestException(
                f"The view type '{self._type}' is not a valid ViewType")

        self._check_view_specs()
        self._technical_info = TechnicalInfoDict()

    def _check_view_specs(self) -> None:
        """This method checks that the view specs are ok

        :raises Exception: [description]
        """
        if self._specs is None:
            return

        if not self._specs.all_config_are_optional():
            raise Exception(
                f"Some specs of the view '{self.__class__.__name__}' are not optional. All the view specs must be optional or have a default value")

    def set_title(self, title: str):
        """ Set title """
        self._title = title

    def get_title(self) -> Optional[str]:
        """ Get title """
        return self._title

    def set_favorite(self, favorite: bool):
        """ Set favorite """
        self._favorite = favorite

    def is_favorite(self) -> bool:
        """ Is favorite """
        return self._favorite

    def get_type(self) -> ViewType:
        """ Get type """
        return self._type

    def set_technical_info_dict(self, technical_info: TechnicalInfoDict):
        """ Set technical info """
        self._technical_info = technical_info

    def get_technical_info_dict(self) -> TechnicalInfoDict:
        """ Get technical info """
        return self._technical_info

    def add_technical_info(self, technical_info: TechnicalInfo):
        """ Add technical info """
        self._technical_info.add(technical_info)

    def get_technical_info(self, key: str) -> TechnicalInfo:
        """ Get technical info dict """
        return self._technical_info.get(key)

    def get_style(self) -> TypingStyle:
        """ Get style """
        return self._style

    def set_style(self, style: TypingStyle):
        """ Set typing style for this view instance. This overrides the style defines in the view decorator and the default style of the view type
        With this you can define a custom style for a specific view instance when you view is generic.
        """
        self._style = style

    def disable_pagination(self):
        """
        Mark the view as not interactive, disable the pagination
        """
        self._disable_pagination = True

    def is_pagination_disabled(self) -> bool:
        """ Is interaction disabled """
        return self._disable_pagination

    def copy_info(self, view: 'View'):
        """
        Copy the view information from another view

        :param view: view to copy the information from
        :type view: View
        """
        self._title = view.get_title()
        self._technical_info = view.get_technical_info_dict()
        self._style = view.get_style()
        self._disable_pagination = view.is_pagination_disabled()
        self._favorite = view.is_favorite()

    @final
    def to_dto(self, params: ConfigParams) -> ViewDTO:
        """ Convert to DTO """
        return ViewDTO(
            type=self._type,
            title=self._title,
            technical_info=self._technical_info.serialize(),
            data=self.data_to_dict(params),
        )

    def data_to_dict(self, params: ConfigParams) -> dict:
        """ Convert to dictionary """
        return {}

    @classmethod
    def json_is_from_view(cls, json_: Any) -> bool:
        """
        Method that return true is the provided json is a json of a view
        """

        if json_ is None or not isinstance(json_, dict):
            return False

        # check type
        if "type" not in json_ or json_["type"] is None or not isinstance(json_["type"], str):
            return False

        # Check data
        if "data" not in json_ or json_["data"] is None:
            return False

        # check that the view type is valid
        try:
            StringHelper.to_enum(ViewType, json_["type"])
        except:
            return False

        return True

    @classmethod
    def generate_range(cls, length: int) -> List[int]:
        """Generate range list like 0,1,2...length
        """
        return list(range(0, length))

    @classmethod
    def get_specs(cls) -> ConfigSpecs:
        return cls._specs
