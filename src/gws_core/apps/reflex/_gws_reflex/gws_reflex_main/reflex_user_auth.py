from gws_core.core.model.model_dto import BaseModelDTO


class ReflexUserAuthInfo(BaseModelDTO):
    """Object send to front to enable authentication to the GLAB api.

    Args:
        BaseModelDTO (_type_): _description_
    """

    app_id: str
    user_access_token: str
