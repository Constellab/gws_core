"""DTOs for the OAuth consent flow."""

from gws_core.core.model.model_dto import BaseModelDTO


class OAuthConsentDetailsDTO(BaseModelDTO):
    """What the user is about to authorize, as the consent page must present it.

    The front-end renders this verbatim rather than hardcoding copy: the backend is
    the only party that knows which client is asking and what a token would actually
    grant it. Keeping the wording here means it cannot drift from what is really
    issued (see ``access_level``).
    """

    client_name: str
    client_id: str
    # Client metadata is self-declared at registration, which is open: a client may
    # call itself anything. The front-end must present the name as an unverified
    # claim while this is False.
    client_name_is_verified: bool

    resource_name: str
    lab_url: str
    user_email: str

    # "full"    -> the token is a full lab session (no scope enforcement)
    # "scoped"  -> the token is limited to the granted scopes
    access_level: str
    access_summary: str
    access_details: list[str]
    # Shown prominently when set. Present precisely when the grant is broader than a
    # user would assume from the client's request.
    warning: str | None = None
