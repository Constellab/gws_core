from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from gws_core.credentials.credentials_type import CredentialsDataBase


class CredentialsRegistry:
    """Global in-memory registry of :class:`CredentialsDataBase` subclasses.

    Populated at import time by the ``@credentials_type`` decorator. It is
    indexed by the globally unique ``type_id`` (``<brick_name>.<unique_name>``)
    of each credentials data class. Any brick can register its own credentials
    data class, so the set of available credentials types is no longer hardcoded.
    """

    # type_id -> credentials data class
    _data_types: "dict[str, type[CredentialsDataBase]]" = {}

    # Legacy type ids that predate the '<brick_name>.<unique_name>' scheme
    # (old uppercase ``CredentialsType`` enum values). Kept so credentials rows
    # written before the 0.23.0 migration still resolve at read time. This is
    # required at boot: lazy db managers read their ``docker_..._db`` credentials
    # to build the db config *before* the 0.23.0 migration rewrites the rows, and
    # the migration itself may run against a lazy db (which must connect first).
    # The 0.23.0 migration normalizes the stored values; this map is the safety
    # net that lets the legacy values resolve in the meantime.
    _legacy_aliases: "dict[str, str]" = {
        "BASIC": "gws_core.basic",
        "S3": "gws_core.s3",
        "S3_LAB_SERVER": "gws_core.s3_lab_server",
        "LAB": "gws_core.lab",
        "OTHER": "gws_core.other",
    }

    @classmethod
    def register(cls, data_class: "type[CredentialsDataBase]") -> None:
        """Register a credentials data class. Called by the decorator.

        Raises if a data class with the same ``type_id`` is already registered,
        which means two credentials data classes of the same brick share a name.
        """
        type_id = data_class.get_type_id()

        if type_id in cls._data_types:
            existing = cls._data_types[type_id]
            raise Exception(
                f"2 credentials data classes register with the same id '{type_id}'. "
                f"Already registered: {existing.__name__}. "
                f"Trying to register: {data_class.__name__}. "
                f"Please update the name passed to @credentials_type."
            )

        cls._data_types[type_id] = data_class

    @classmethod
    def get_data_type(cls, type_id: str) -> "type[CredentialsDataBase] | None":
        """Return the credentials data class registered for the given id, or None.

        Legacy type ids (old uppercase enum values) are resolved through
        :attr:`_legacy_aliases` so rows not yet normalized by the 0.23.0
        migration still resolve.
        """
        type_id = cls._legacy_aliases.get(type_id, type_id)
        return cls._data_types.get(type_id)

    @classmethod
    def get_and_check_data_type(cls, type_id: str) -> "type[CredentialsDataBase]":
        """Return the credentials data class registered for the given id.

        Raises if no data class is registered for the given id.
        """
        data_class = cls.get_data_type(type_id)
        if data_class is None:
            raise Exception(f"Credentials type '{type_id}' is not registered. Was the brick that registered it disabled?"
            )
        return data_class

    @classmethod
    def get_all(cls) -> "dict[str, type[CredentialsDataBase]]":
        """Return all registered credentials data classes, keyed by type id."""
        return dict(cls._data_types)

    @classmethod
    def get_all_ids(cls) -> list[str]:
        """Return the ids of all registered credentials data classes."""
        return list(cls._data_types.keys())
