

from gws_core.config.config_types import ConfigParamsDict
from gws_core.core.exception.exceptions.bad_request_exception import \
    BadRequestException
from gws_core.impl.enote.enote_resource import ENoteResource
from gws_core.resource.resource import Resource
from gws_core.resource.resource_model import ResourceModel
from gws_core.resource.view.view_dto import CallViewResultDTO


class ResourceENoteService():

    @classmethod
    def get_file_path(cls, enote_resource_model_id: str, filename: str) -> str:
        resource_model = ResourceModel.get_by_id_and_check(enote_resource_model_id)

        enote: Resource = resource_model.get_resource()

        if not isinstance(enote, ENoteResource):
            raise BadRequestException('The resource is not an eNote')

        return enote.get_file_path(filename)

    @classmethod
    def call_view_method(cls, enote_resource_model_id: str, sub_resource_key: str,
                         view_name: str, config: ConfigParamsDict) -> CallViewResultDTO:
        resource_model = ResourceModel.get_by_id_and_check(enote_resource_model_id)

        enote: Resource = resource_model.get_resource()

        if not isinstance(enote, ENoteResource):
            raise BadRequestException('The resource is not an eNote')

        return enote.call_view_on_resource(sub_resource_key, view_name, config)
