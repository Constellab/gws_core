# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from peewee import ModelSelect


class Query:
    """
    Query class
    """
    # Todo vérifier que ça fonctione encore bien, le cast a été enlevé
    @classmethod
    def format(cls, query: ModelSelect, view_params: dict = None, as_view: bool = False, as_json: bool = False,
               deep: bool = False):

        if view_params is None:
            view_params = {}

        result = []
        if as_view:
            if as_json:
                for model in query:
                    model = model.model

                    # -> create a new ViewModel is required
                    view_model = model.view(params=view_params)
                    result.append(view_model.to_json(deep=deep))
            else:
                for model in query:
                    model = model.model

                    view_model = model.view(params=view_params)
                    result.append(view_model)
        else:
            if as_json:
                for model in query:
                    result.append(model.to_json(deep=deep))
            else:
                result = query

        return result
