

from gws_core.core.exception.exceptions.bad_request_exception import \
    BadRequestException
from gws_core.impl.enote.enote_resource import ENoteResource
from gws_core.resource.resource_model import ResourceModel


class ResourceENoteService():

    @classmethod
    def get_file_path(cls, enote_resource_model_id: str, filename: str) -> str:
        resource_model = ResourceModel.get_by_id_and_check(enote_resource_model_id)

        enote: ENoteResource = resource_model.get_resource()

        if not isinstance(enote, ENoteResource):
            raise BadRequestException('The resource is not an eNote')

        return enote.get_figure_path(filename)
