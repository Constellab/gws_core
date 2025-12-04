from gws_core.config.config_params import ConfigParams
from gws_core.impl.network.network_type import NetworkDTO
from gws_core.resource.view.view import View
from gws_core.resource.view.view_types import ViewType


class NetworkView(View):
    _type: ViewType = ViewType.NETWORK
    _data: NetworkDTO

    def __init__(self, network_dto: NetworkDTO):
        super().__init__()

        if not isinstance(network_dto, NetworkDTO):
            raise Exception("NetworkView data must be an instance of NetworkDTO")

    def data_to_dict(self, params: ConfigParams) -> dict:
        return self._data.to_json_dict()

    @staticmethod
    def from_dict(data: dict) -> "NetworkView":
        return NetworkView(NetworkDTO.from_json(data))
