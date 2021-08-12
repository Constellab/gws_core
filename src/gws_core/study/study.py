# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from ..model.typing_register_decorator import TypingDecorator
from ..model.viewable import Viewable


@TypingDecorator(unique_name="Study", object_type="GWS_CORE", hide=True)
class Study(Viewable):
    """
    Study class.
    """

    _table_name = 'gws_study'

    def archive(self, tf: bool) -> bool:
        """
        Deactivated method. Returns False.
        """

        return False

    @classmethod
    def create_default_instance(cls):
        """
        Create the default study of the lab
        """

        cls.get_default_instance()

    @classmethod
    def get_default_instance(cls):
        """
        Get the default study of the lab
        """

        try:
            study = Study.get_by_id(1)
        except Exception as _:
            study = Study(
                data={
                    "title": "Default study",
                    "description": "The default study of the lab"
                }
            )
            study.save()

        return study
