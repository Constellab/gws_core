# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

class Query:
    """
    Query class
    """

    @classmethod
    def format(cls, Q, view_params: dict = {}, as_view: bool = False, as_json: bool = False, shallow: bool = False):
        _Q = []
        from ...model.view_model import ViewModel
        if as_view:
            if as_json:
                for model in Q:
                    if isinstance(model, ViewModel):
                        model = model.model
                    else:
                        model = model.cast()

                    # -> create a new ViewModel is required
                    view_model = model.view(params=view_params)
                    _Q.append(view_model.to_json(shallow=shallow))
            else:
                for model in Q:
                    if isinstance(model, ViewModel):
                        model = model.model
                    else:
                        model = model.cast()

                    view_model = model.view(params=view_params)
                    _Q.append(view_model)
        else:
            if as_json:
                for model in Q:
                    _Q.append(model.to_json(shallow=shallow))
            else:
                _Q = Q

        return _Q
