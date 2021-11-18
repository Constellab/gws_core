# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from peewee import ModelSelect


class Query():
    """
    Query class
    """
    @classmethod
    def format(cls, query: ModelSelect,  as_json: bool = False, deep: bool = False):

        result = []

        if as_json:
            for model in query:
                result.append(model.to_json(deep=deep))
        else:
            result = query

        return result
