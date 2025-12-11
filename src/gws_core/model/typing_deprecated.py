from gws_core.core.db.version import Version
from gws_core.core.model.model_dto import BaseModelDTO


class TypingDeprecated(BaseModelDTO):
    """
    Object to provide when a typing is deprecated.
    """

    deprecated_since: str
    deprecated_message: str

    def check_version(self) -> bool:
        """Check if the version if valid"""
        try:
            Version(self.deprecated_since)
            return True
        except:
            return False
