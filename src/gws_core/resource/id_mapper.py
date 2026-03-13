from typing import overload
from uuid import uuid4

from gws_core.share.shared_dto import ShareEntityCreateMode


class IdMapper:
    """Utility class to manage mapping of old IDs to new IDs during resource import."""

    _id_mapping: dict[str, str]
    _create_mode: ShareEntityCreateMode

    def __init__(self, _create_mode: ShareEntityCreateMode):
        self._id_mapping = {}
        self._create_mode = _create_mode

    @overload
    def generate_new_id(self, old_id: str) -> str: ...
    @overload
    def generate_new_id(self, old_id: None) -> None: ...
    def generate_new_id(self, old_id: str | None) -> str | None:
        """Generate a new UUID for an old ID and store the mapping."""
        if old_id is None:
            return None
        if self._create_mode == ShareEntityCreateMode.KEEP_ID:
            return old_id

        if old_id in self._id_mapping:
            return self._id_mapping[old_id]
        new_id = str(uuid4())
        self._id_mapping[old_id] = new_id
        return new_id
