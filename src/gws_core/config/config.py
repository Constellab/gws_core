# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import Union, final

from gws_core.model.typing_register_decorator import TypingDecorator

from ..core.classes.validator import Validator
from ..core.exception.exceptions import BadRequestException
from ..model.viewable import Viewable


@final
@TypingDecorator(unique_name="Config", object_type="GWS_CORE", hide=True)
class Config(Viewable):
    """
    Config class that represents the configuration of a process. A configuration is
    a collection of parameters
    """

    _table_name = 'gws_config'

    def __init__(self, *args, specs: dict = None, **kwargs):
        super().__init__(*args, **kwargs)

        if not self.id:
            self.data = {
                "specs": {},
                "params": {}
            }

        if specs:
            if not isinstance(specs, dict):
                raise BadRequestException(f"The specs must be a dictionnary")

            # convert type to str

            for k in specs:
                if isinstance(specs[k]["type"], type):
                    specs[k]["type"] = specs[k]["type"].__name__

                default = specs[k].get("default", None)
                if not default is None:
                    #param_t = specs[k]["type"]
                    try:
                        validator = Validator.from_specs(**specs[k])
                        default = validator.validate(default)
                        specs[k]["default"] = default
                    except Exception as err:
                        raise BadRequestException(
                            f"Invalid default config value. Error message: {err}") from err

            self.set_specs(specs)

    # -- A --

    def archive(self, archive: bool) -> bool:
        """
        Archive the config

        :param tf: True to archive, False to unarchive
        :type: `bool`
        :return: True if successfully archived, False otherwise
        :rtype: `bool`
        """

        from ..process.process_model import ProcessModel

        # todo a vérifier, une config peut être utilisé par plusieurs process?
        some_processes_are_in_invalid_archive_state = ProcessModel.select().where(
            (ProcessModel.config == self) & (
                ProcessModel.is_archived == (not archive))
        ).count()

        if some_processes_are_in_invalid_archive_state:
            return False

        return super().archive(archive)

    # -- C --

    # -- D --

    # -- G --

    def get_param(self, name: str) -> Union[str, int, float, bool, list, dict]:
        """
        Returns the value of a parameter by its name

        :param name: The name of the parameter
        :type: str
        :return: The value of the parameter (base type)
        :rtype: `str`, `int`, `float`, `bool`
        """
        if not name in self.specs:
            raise BadRequestException(f"Parameter {name} does not exist")

        default = self.specs[name].get("default", None)
        return self.data.get("params", {}).get(name, default)

    # -- P --

    @property
    def params(self) -> dict:
        """
        Returns all the parameters

        :return: The parameters
        :rtype: `dict`
        """

        params = self.data["params"]
        specs = self.data["specs"]
        for k in specs:
            if not k in params:
                default = specs[k].get("default", None)
                if default:
                    params[k] = default

        return params

    def param_exists(self, name: str) -> bool:
        """
        Test if a parameter exists

        :return: True if the parameter exists, False otherwise
        :rtype: `bool`
        """

        return name in self.data.get("specs", {})

    # -- R --

    # -- S --

    def set_param(self, name: str, value: Union[str, int, float, bool]):
        """
        Sets the value of a parameter by its name

        :param name: The name of the parameter
        :type: str
        :param value: The value of the parameter (base type)
        :type: [str, int, float, bool, NoneType]
        """

        if not name in self.specs:
            raise BadRequestException(f"Parameter '{name}' does not exist.")

        #param_t = self.specs[name]["type"]

        try:
            validator = Validator.from_specs(**self.specs[name])
            value = validator.validate(value)
        except Exception as err:
            raise BadRequestException(
                f"Invalid parameter value '{name}'. Error message: {err}") from err

        if not "params" in self.data:
            self.data["params"] = {}

        self.data["params"][name] = value

    def set_params(self, params: dict):
        """
        Set config parameters
        """

        for k in params:
            self.set_param(k, params[k])

    @property
    def specs(self) -> dict:
        """
        Returns config specs
        """

        return self.data["specs"]

    def set_specs(self, specs: dict):
        """
        Sets the specs of the config (remove current parameters)

        :param specs: The config specs
        :type: dict
        """

        if not isinstance(specs, dict):
            raise BadRequestException("The specs must be a dictionary.")

        if self.id:
            raise BadRequestException(
                "Cannot alter the specs of a saved config")

        self.data["specs"] = specs

    # -- T --
    def to_json(self, shallow=False, bare: bool = False, **kwargs) -> dict:
        """
        Returns JSON string or dictionnary representation of the model.

        :param stringify: If True, returns a JSON string. Returns a python dictionary otherwise. Defaults to False
        :type stringify: bool
        :param prettify: If True, indent the JSON string. Defaults to False.
        :type prettify: bool
        :return: The representation
        :rtype: dict, str
        """

        _json = super().to_json(shallow=shallow, bare=bare, **kwargs)
        if shallow:
            del _json["data"]

        return _json

    # -- V --
