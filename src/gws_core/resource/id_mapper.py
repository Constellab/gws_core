from uuid import uuid4

from git import Optional


class IdMapper:
    """Utility class to manage mapping of old IDs to new IDs during resource import."""

    def __init__(self):
        self._id_mapping = {}

    def generate_new_id(self, old_id: str) -> str:
        """Generate a new UUID for an old ID and store the mapping."""
        if old_id in self._id_mapping:
            return self._id_mapping[old_id]
        new_id = str(uuid4())
        self._id_mapping[old_id] = new_id
        return new_id

    def get_new_id(self, old_id: str | None) -> Optional[str]:
        """Get the new ID corresponding to an old ID, or None if not found."""
        if old_id is None:
            return None
        return self._id_mapping.get(old_id)

    def set_mapping(self, old_id: str, new_id: str) -> None:
        """Explicitly set a mapping from an old ID to a new ID."""
        self._id_mapping[old_id] = new_id

    def has_mapping(self, old_id: str) -> bool:
        """Check if there is a mapping for the given old ID."""
        return old_id in self._id_mapping
