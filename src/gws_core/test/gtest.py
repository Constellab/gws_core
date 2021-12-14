# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from gws_core.study.study import Study

from ..core.console.console import Console


class GTest(Console):
    """
    GTest class.

    Provides functionalities to initilize unit testing environments
    """

    @classmethod
    def create_default_study(cls) -> Study:
        """
        Get a default study DTO
        """
        return Study(title="Default study", description="Study description").save()
