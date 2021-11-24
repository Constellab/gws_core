# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from ....resource.resource_decorator import resource_decorator
from ..table import Table


@resource_decorator("EncodedTable")
class EncodedTable(Table):
    pass
