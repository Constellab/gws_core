# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import Generic, TypeVar

from peewee import ModelSelect

from ...model.viewable import Viewable

QueryType = TypeVar('QueryType', bound=Viewable)


class Query(Generic[QueryType]):
    """
    Query class
    """
    @classmethod
    def format(cls, query: ModelSelect, view_params: dict = None, as_view: bool = False, as_json: bool = False,
               deep: bool = False):

        if view_params is None:
            view_params = {}

        result = []
        if as_view:
            if as_json:
                for model in query:
                    model: QueryType = model.model

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
