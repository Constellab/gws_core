# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from ...core.classes.search_builder import SearchBuilder
from .view_config import ViewConfig


class ViewConfigSearchBuilder(SearchBuilder):
    """Search build for the view cofnig

    :param SearchBuilder: [description]
    :type SearchBuilder: [type]
    """

    def __init__(self) -> None:
        super().__init__(ViewConfig, default_order=[ViewConfig.last_modified_at.desc()])
