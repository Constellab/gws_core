from collections.abc import Callable
from typing import TYPE_CHECKING

from gws_core.brick.brick_helper import BrickHelper
from gws_core.core.utils.string_helper import StringHelper
from gws_core.credentials.credentials_registry import CredentialsRegistry

if TYPE_CHECKING:
    from gws_core.credentials.credentials_type import CredentialsDataBase


def credentials_type(
    unique_name: str,
    human_name: str | None = None,
    short_description: str | None = None,
) -> Callable:
    """Decorator that registers a :class:`CredentialsDataBase` subclass.

    :param unique_name: identifier for the credentials data class. It must be
        unique within the brick that declares it: no two credentials data classes
        in the same brick can share the same ``unique_name``. It is automatically
        prefixed with the owning brick name (derived from the module path, like
        the typing system) to form a globally unique ``type_id`` of the form
        ``<brick_name>.<unique_name>``. That ``type_id`` is what gets stored in
        the ``gws_credentials.type`` column.

        The ``unique_name`` must contain only alphanumeric characters and
        underscores (same rule as a task ``unique_name``). In particular it must
        not contain a dot, as the dot is the namespace separator.
    :param human_name: human readable name of the credentials type, shown in the
        interface. Defaults to the ``unique_name`` when not provided.
    :param short_description: short description of the credentials type, shown in
        the interface.

    Example (declared in the gws_core brick)::

        @credentials_type("s3", human_name="S3", short_description="S3 storage credentials")
        class CredentialsDataS3(CredentialsDataBase):
            ...

        # registered type_id -> "gws_core.s3"
    """

    def decorator(data_class: "type[CredentialsDataBase]") -> "type[CredentialsDataBase]":
        # CredentialsDataBase defines get_type_id, which reads the id set just below.
        # A class missing it is not a CredentialsDataBase subclass.
        if not hasattr(data_class, "get_type_id"):
            raise Exception(
                f"The class '{data_class.__name__}' decorated with "
                f"@credentials_type must extend CredentialsDataBase."
            )
        if not unique_name or not StringHelper.is_alphanumeric(unique_name):
            raise Exception(
                f"The credentials type name '{unique_name}' is not valid. It must "
                f"contain only alphanumeric characters and underscores ('_')."
            )

        # prefix with the brick name to make the type id globally unique
        brick_name = BrickHelper.get_brick_name(data_class)
        data_class.__credentials_type_name__ = unique_name
        data_class.__credentials_type_id__ = f"{brick_name}.{unique_name}"
        data_class.__credentials_type_brick_name__ = brick_name
        data_class.__credentials_type_human_name__ = human_name or unique_name
        data_class.__credentials_type_short_description__ = short_description

        CredentialsRegistry.register(data_class)
        return data_class

    return decorator
