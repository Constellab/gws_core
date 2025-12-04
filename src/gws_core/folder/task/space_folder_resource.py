from gws_core.config.config_params import ConfigParamsDict
from gws_core.folder.space_folder import SpaceFolder
from gws_core.impl.json.json_view import JSONView
from gws_core.model.typing_style import TypingStyle
from gws_core.resource.r_field.primitive_r_field import StrRField
from gws_core.resource.resource import Resource
from gws_core.resource.resource_decorator import resource_decorator
from gws_core.resource.view.view_decorator import view


@resource_decorator(
    "SpaceFolderResource",
    human_name="Space folder resource",
    short_description="Resource to reference a space folder",
    style=TypingStyle.material_icon("folder", background_color="#6C4EF6"),
)
class SpaceFolderResource(Resource):
    """Resource to reference a space folder.

    :param Resource: _description_
    :type Resource: _type_
    :return: _description_
    :rtype: _type_
    """

    space_folder_id: str = StrRField()

    _space_folder: SpaceFolder = None

    def __init__(self, space_folder_id: str = None):
        super().__init__()
        self.space_folder_id = space_folder_id

    def get_space_folder(self) -> SpaceFolder:
        if self._space_folder is None:
            self._space_folder = SpaceFolder.get_by_id_and_check(self.space_folder_id)
        return self._space_folder

    @view(view_type=JSONView, human_name="View space folder info", default_view=True)
    def view_space_folder(self, config: ConfigParamsDict = None) -> JSONView:
        return JSONView(
            {
                "id": self.space_folder_id,
                "name": self.get_space_folder().name,
            }
        )
