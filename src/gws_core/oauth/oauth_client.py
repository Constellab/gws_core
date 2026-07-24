"""Persistence for the OAuth clients registered against the lab.

Why this is in the database rather than in memory
-------------------------------------------------
A client registers itself once (Dynamic Client Registration) and then **caches its
``client_id`` indefinitely** -- Claude Code, for instance, keeps it in
``~/.claude.json``. Holding the registry in memory therefore breaks on the first
lab restart: the client keeps presenting an id the new process has never seen, and
``/authorize`` answers "Client ID '...' not found". The client cannot recover on
its own, because it has no reason to think its id went stale, so the failure is
permanent rather than a one-off re-login.

The other OAuth state (pending logins, authorization codes) legitimately stays in
memory: it lives for seconds to minutes, and losing it on a restart only costs a
retry of a login that was in flight.
"""

from typing import Any

from gws_core.core.model.model import Model
from gws_core.core.model.typed_db_field import TypedCharField, TypedJSONField


class OAuthClient(Model):
    """An OAuth client registered against the lab.

    The client metadata is stored as the raw JSON the OAuth library gave us
    (``OAuthClientInformationFull``, a model of RFC 7591), so that library stays
    the single owner of the schema: it is round-tripped verbatim rather than
    mirrored into columns that would drift as the spec evolves.
    """

    client_id: TypedCharField = TypedCharField(unique=True, max_length=255)
    client_info: TypedJSONField = TypedJSONField()

    @classmethod
    def find_by_client_id(cls, client_id: str) -> "OAuthClient | None":
        return cls.get_or_none(cls.client_id == client_id)

    @classmethod
    def save_client(cls, client_id: str, client_info: dict[str, Any]) -> "OAuthClient":
        """Insert or update the stored metadata for ``client_id``."""
        existing = cls.find_by_client_id(client_id)
        if existing is not None:
            existing.client_info = client_info
            return existing.save()

        return cls(client_id=client_id, client_info=client_info).save()

    class Meta:
        table_name = "gws_oauth_client"
        is_table = True
