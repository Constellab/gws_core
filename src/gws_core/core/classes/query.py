# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from peewee import ModelSelect

from ...model.view_model import ViewModel


class Query:
    """
    Query class
    """

    @classmethod
    def format(cls, query: ModelSelect, view_params: dict = None, as_view: bool = False, as_json: bool = False, shallow: bool = False):

        if view_params is None:
            view_params = {}

        result = []
        if as_view:
            if as_json:
                for model in query:
                    if isinstance(model, ViewModel):
                        model = model.model
                    else:
                        model = model.cast()

                    # -> create a new ViewModel is required
                    view_model = model.view(params=view_params)
                    result.append(view_model.to_json(shallow=shallow))
            else:
                for model in query:
                    if isinstance(model, ViewModel):
                        model = model.model
                    else:
                        model = model.cast()

                    view_model = model.view(params=view_params)
                    result.append(view_model)
        else:
            if as_json:
                for model in query:
                    result.append(model.to_json(shallow=shallow))
            else:
                result = query

        return result
