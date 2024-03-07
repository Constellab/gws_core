# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from gws_core.core.model.model_dto import BaseModelDTO


class TypingDeprecated(BaseModelDTO):
    """
    Object to provide when a typing is deprecated.
    """

    deprecated_since: str
    deprecated_message: str

    def __init__(self,
                 deprecated_since: str,
                 deprecated_message: str):
        """_summary_

        :param deprecated_since: Version of this object brick since this typing is deprecated.
          It must be a version string like 1.0.0.
        :type deprecated_since: str
        :param deprecated_message: Message about the deprecation. For example you can provide the name of another object to use instead.
        :type deprecated_message: str
        """
        self.deprecated_since = deprecated_since
        self.deprecated_message = deprecated_message
