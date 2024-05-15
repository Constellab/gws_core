

from gws_core.core.model.model_dto import BaseModelDTO


class CredentialsDataBiolector(BaseModelDTO):
    """Format of the data for biolector credentials"""
    endpoint_url: str
    secure_channel: bool
