# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import json
from peewee import CharField

from gws.exception.bad_request_exception import BadRequestException
from .activity import Activity
from .db.model import Model

# ####################################################################
#
# ViewModel class
#
# ####################################################################

class ViewModel(Model):
    """
    ViewModel class. A view model is parametrized representation of the orginal data

    :property model_uri: the uri of the related Model
    :type model_uri: `str`
    :property model_type: the type of the related Model
    :type model_type: `str`
    """

    model_uri = CharField(index=True)
    model_type = CharField(index=True)

    _model = None
    _is_transient = False    # transient view model are used to temprarily view part of a model (e.g. stream view)
    _table_name = 'gws_view_model'

    def __init__(self, *args, model: Model = None, **kwargs):
        super().__init__(*args, **kwargs)
        if isinstance(model, Model):
            self._model = model
        if not self.id is None:
            self._model = self.model
        if not "params" in self.data or self.data["params"] is None:
            self.data["params"] = {}

    # -- A --

    # -- C --

    # -- D --

    @property
    def description(self) -> str:
        """
        Returns the description. Alias of :meth:`get_description`

        :return: The description
        :rtype: str
        """

        return self.get_description()

    # -- F --

    # -- G --

    def get_param(self, key: str, default=None) -> str:
        """
        Get a parameter using its key

        :param key: The key of the parameter
        :type key: `str`
        :param default: The default value to return if the key does not exist. Defaults to `None`.
        :type default: `str`
        :return: The value of the parameter
        :rtype: `str`
        """

        return self.data["params"].get(key, default)

    # -- H --

    # -- M --

    @property
    def model(self) -> Model:
        """
        Get the Model of the ViewModel.

        :return: The model instance
        :rtype: `gws.db.model.Model`
        """

        from .service.model_service import ModelService

        if not self._model is None:
            return self._model
        model_t = ModelService.get_model_type(self.model_type)
        model = model_t.get(model_t.uri == self.model_uri)
        self._model = model.cast()
        return self._model

    # -- P --

    @property
    def params(self) -> dict:
        """
        Get the parameter set

        :return: The parameter set
        :rtype: `dict`
        """

        return self.data["params"]

    # -- R --

    def render(self) -> dict:
        """
        Render the ViewModel

        :return: The rendering
        :rtype: `dict`
        """

        model = self.model
        fn = self.data.get("render", "as_json")
        params = self.data.get("params", {})
        try:
            func = getattr(model, "render__" + fn)
            return func(**params)
        except Exception as err:
            raise BadRequestException(f"Cannot create the ViewModel rendering. Error: {err}.")

    # -- S --

    def set_param(self, key, value):
        self.data["params"][key] = value

    def set_params(self, params: dict={}):
        if params is None:
            params = {}
        if not isinstance(params, dict):
            raise BadRequestException("Parameter must be a dictionnary")
        self.data["params"] = params

    def set_model(self, model: None):
        if not self.model_uri is None:
            raise BadRequestException("A model already exists")
        self._model = model
        if model.is_saved():
            self.model_uri = model.uri

    def save(self, *args, **kwargs):
        """
        Saves the view model
        """

        if self._is_transient:
            return True
        if self._model is None:
            raise BadRequestException("The ViewModel has no model")
        else:
            if not self.model_uri is None and self._model.uri != self.model_uri:
                raise BadRequestException("It is not allowed to change model of the ViewModel that is already saved")

            if not self._model.save(*args, **kwargs):
                raise BadRequestException("Cannot save the vmodel. Please ensure that the model of the vmodel is saved before")
            self.model_uri = self._model.uri
            self.model_type = self._model.full_classname()
            return super().save(*args, **kwargs)


    # -- T --

    # -- U --

    def update(self, data:dict, track_activity:bool = True):
        """
        Update the ViewModel with new data
        """

        params = data.get("params", {})
        self.set_params(params)
        for k in data:
            if k != "params":
                self.data[k] = data[k]
        if track_activity:
            Activity.add(
                Activity.UPDATE,
                object_type = self.full_classname(),
                object_uri = self.uri
            )
        self.save()

    # -- V --

    def to_json(self, *, stringify: bool=False, prettify: bool=False, **kwargs) -> (str, dict, ):
        """
        Returns JSON string or dictionnary representation of the model.

        :param stringify: If True, returns a JSON string. Returns a python dictionary otherwise. Defaults to False
        :type stringify: bool
        :param prettify: If True, indent the JSON string. Defaults to False.
        :type prettify: bool
        :return: The representation
        :rtype: dict, str
        """

        _json = super().to_json(**kwargs)
        _json["model"] = {
            "uri": _json["model_uri"],
            "type": _json["model_type"],
            "rendering": self.render()
        }
        del _json["model_uri"]
        del _json["model_type"]
        if not self.is_saved():
            _json["uri"] = ""
            _json["save_datetime"] = ""
        if stringify:
            if prettify:
                return json.dumps(_json, indent=4)
            else:
                return json.dumps(_json)
        else:
            return _json


# ####################################################################
#
# StreamViewModel class
#
# ####################################################################

class StreamViewModel(ViewModel):
    _is_transient = True

    # -- G --

    #def get_instance( model, params ):
    #    vm = ViewModel(model=model)
    #    vm.set_params(params)
    #    return vm
