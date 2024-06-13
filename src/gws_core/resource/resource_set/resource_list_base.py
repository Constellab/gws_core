
from __future__ import annotations

from abc import abstractmethod
from typing import TYPE_CHECKING, Dict, List, Set

from gws_core.config.config_params import ConfigParams
from gws_core.impl.view.resources_list_view import ResourcesListView
from gws_core.model.typing_style import TypingStyle
from gws_core.resource.technical_info import TechnicalInfo
from gws_core.resource.view.view_decorator import view

from ..resource import Resource
from ..resource_decorator import resource_decorator

if TYPE_CHECKING:
    from ..resource_model import ResourceModel


@resource_decorator(unique_name="ResourceListBase", human_name="Resource list base",
                    short_description="Abstract class for resource list", hide=True,
                    style=TypingStyle.material_icon("format_list_bulleted", background_color="#FEC7B4"))
class ResourceListBase(Resource):
    """Abstract class for resource list, to use only if you want you're doing.
    By default the sytem create a new
    resource for each resource in the set when saving the set
    """

    # list the resource ids that are constant (the system doesn't create new resources on save)
    __constant_resource_ids__: Set[str] = None

    @abstractmethod
    def get_resource_ids(self) -> Set[str]:
        raise NotImplementedError()

    @abstractmethod
    def get_resources_as_set(self) -> Set[Resource]:
        pass

    @abstractmethod
    def replace_resources_by_model_id(self, resources: Dict[str, Resource]) -> None:
        """Replace current resources by the resources in the dict

        :param resources: dict where key is the resource model id and value is the resource
        :type resources: Dict[str, Resource]
        """

    def __resource_is_constant__(self, resource_uid: str) -> bool:
        """return true if the resource is constant and was create before
        a task that generated this resource set
        """
        return self.__constant_resource_ids__ is not None and resource_uid in self.__constant_resource_ids__

    def _get_resource_by_model_id(self, resource_model_id: str) -> Resource:
        if not resource_model_id in self.get_resource_ids():
            raise Exception(f"The resource with id {resource_model_id} is not in the resource list")

        from ..resource_model import ResourceModel
        return ResourceModel.get_by_id_and_check(resource_model_id).get_resource()

    @abstractmethod
    def __set_r_field__(self) -> None:
        """This method is called before the save of this resource but after the save of the
        child resources. Set the r_field of this resource with the ids of the child

        :raises NotImplementedError: _description_
        """
        raise NotImplementedError()

    def _load_resources(self) -> Set[Resource]:
        resource_models: List[ResourceModel] = self.get_resource_models()

        resources: Set[Resource] = set()
        for resource_model in resource_models:
            resources.add(resource_model.get_resource())
        return resources

    def get_resource_models(self) -> List[ResourceModel]:
        from ..resource_model import ResourceModel
        resource_ids = list(self.get_resource_ids())

        if not resource_ids:
            return list()

        return list(ResourceModel.select().where(ResourceModel.id.in_(resource_ids))
                    .order_by(ResourceModel.name))

    @view(view_type=ResourcesListView, human_name='Resources list',
          short_description='List the resources', default_view=True)
    def view_resources_list(self, params: ConfigParams) -> ResourcesListView:
        view = ResourcesListView()
        view.add_resources(self.get_resource_models())
        view.add_technical_info(TechnicalInfo('Number of resources',
                                              len(self.get_resources_as_set())))
        return view

    def __len__(self) -> int:
        return len(self.get_resources_as_set())
