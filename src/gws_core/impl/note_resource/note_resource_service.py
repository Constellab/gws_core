from gws_core.config.config_params import ConfigParamsDict
from gws_core.core.exception.exceptions.bad_request_exception import BadRequestException
from gws_core.impl.note_resource.note_resource import NoteResource
from gws_core.resource.resource import Resource
from gws_core.resource.resource_model import ResourceModel
from gws_core.resource.view.view_dto import CallViewResultDTO


class NoteResourceService:
    @classmethod
    def get_file_path(cls, note_resource_model_id: str, filename: str) -> str:
        resource_model = ResourceModel.get_by_id_and_check(note_resource_model_id)

        note_resource: Resource = resource_model.get_resource()

        if not isinstance(note_resource, NoteResource):
            raise BadRequestException("The resource is not an note")

        return note_resource.get_file_path(filename)

    @classmethod
    def call_view_method(
        cls,
        note_resource_model_id: str,
        sub_resource_key: str,
        view_name: str,
        config: ConfigParamsDict,
    ) -> CallViewResultDTO:
        resource_model = ResourceModel.get_by_id_and_check(note_resource_model_id)

        note_resource: Resource = resource_model.get_resource()

        if not isinstance(note_resource, NoteResource):
            raise BadRequestException("The resource is not an note")

        return note_resource.call_view_on_resource(sub_resource_key, view_name, config)
