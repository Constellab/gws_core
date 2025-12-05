from __future__ import annotations

from abc import abstractmethod
from typing import TYPE_CHECKING, final

from gws_core.config.config_params import ConfigParams
from gws_core.impl.view.resources_list_view import ResourcesListView
from gws_core.model.typing_style import TypingStyle
from gws_core.resource.resource_dto import ResourceOrigin
from gws_core.resource.technical_info import TechnicalInfo
from gws_core.resource.view.view_decorator import view

from ..resource import Resource
from ..resource_decorator import resource_decorator

if TYPE_CHECKING:
    from gws_core.scenario.scenario import Scenario
    from gws_core.task.task_model import TaskModel

    from ..resource_model import ResourceModel


@resource_decorator(
    unique_name="ResourceListBase",
    human_name="Resource list base",
    short_description="Abstract class for resource list",
    hide=True,
    style=TypingStyle.material_icon("format_list_bulleted", background_color="#FEC7B4"),
)
class ResourceListBase(Resource):
    """Abstract class for resource list, to use only if you want you're doing.
    By default the sytem create a new
    resource for each resource in the set when saving the set
    """

    # list the resource uids (not model id) that are constant (the system doesn't create new resources on save)
    __constant_resource_uids__: set[str] = None

    def init(self) -> None:
        # On init, mark the existing resources of the resource list
        # as constant resources, so if this resource is saved on task output,
        # the existing sub resources are not created again
        self.__constant_resource_uids__ = set()
        for resource in self.get_resources_as_set():
            self.__constant_resource_uids__.add(resource.uid)

    @abstractmethod
    def get_resource_model_ids(self) -> set[str]:
        """
        Return the resource model ids of the sub resources

        :return: set of resource model ids
        :rtype: Set[str]
        """
        raise NotImplementedError()

    @abstractmethod
    def get_resources_as_set(self) -> set[Resource]:
        """
        Return the sub resources as a set

        :return: set of resources
        :rtype: Set[Resource]
        """

    @abstractmethod
    def replace_resources_by_model_id(self, resources: dict[str, Resource]) -> None:
        """
        Replace current resources by the resources in the dict

        :param resources: dict where key is the resource model id and value is the resource
        :type resources: Dict[str, Resource]
        """

    def has_resource_model(self, resource_model_id: str) -> bool:
        """
        Return true if the resource with the given id is in the resource list

        :param resource_model_id: id of the ResourceModel
        :type resource_model_id: str
        :return: True if the resource with the given id is in the resource list
        :rtype: bool
        """
        return resource_model_id in self.get_resource_model_ids()

    def __resource_is_constant__(self, resource_uid: str) -> bool:
        """return true if the resource is constant and was create before
        a task that generated this resource set
        """
        return (
            self.__constant_resource_uids__ is not None
            and resource_uid in self.__constant_resource_uids__
        )

    def _get_resource_by_model_id(self, resource_model_id: str) -> Resource:
        if resource_model_id not in self.get_resource_model_ids():
            raise Exception(f"The resource with id {resource_model_id} is not in the resource list")

        from ..resource_model import ResourceModel

        return ResourceModel.get_by_id_and_check(resource_model_id).get_resource()

    @abstractmethod
    def __set_r_field__(self, ids_map: dict[str, str]) -> None:
        """This method is called before the save of this resource but after the save of the
        child resources. Set the r_field of this resource with the ids of the child

        :param ids_map: dict where key is the resource uid and value is the resource model id
        :type ids_map: Dict[str, str]
        :raises NotImplementedError: _description_
        """
        raise NotImplementedError()

    @final
    def save_new_children_resources(
        self,
        resource_origin: ResourceOrigin,
        scenario: Scenario = None,
        task_model: TaskModel = None,
        port_name: str = None,
    ) -> list[ResourceModel]:
        from ..resource_model import ResourceModel

        new_children_resources: list[ResourceModel] = []

        ids_map = {}
        for resource in self.get_resources_as_set():
            # if this is a new resource

            if self.__resource_is_constant__(resource.uid):
                # if the resource is constant, get the model id of the resource
                # from the resource and add it to the map
                ids_map[resource.uid] = resource.get_model_id()
            else:
                # create and save the resource model from the resource
                resource_model = ResourceModel.save_from_resource(
                    resource,
                    origin=resource_origin,
                    scenario=scenario,
                    task_model=task_model,
                    port_name=port_name,
                )
                ids_map[resource.uid] = resource_model.id
                new_children_resources.append(resource_model)
        self.__set_r_field__(ids_map)
        return new_children_resources

    def _load_resources(self) -> set[Resource]:
        resource_models: list[ResourceModel] = self.get_resource_models()

        resources: set[Resource] = set()
        for resource_model in resource_models:
            resources.add(resource_model.get_resource())
        return resources

    def get_resource_models(self) -> list[ResourceModel]:
        """
        Return the resource models of the sub resources list

        :return: list of resource models
        :rtype: List[ResourceModel]
        """
        from ..resource_model import ResourceModel

        resource_ids = list(self.get_resource_model_ids())

        if not resource_ids:
            return list()

        return list(
            ResourceModel.select()
            .where(ResourceModel.id.in_(resource_ids))
            .order_by(ResourceModel.name)
        )

    def _check_resource_before_add(
        self, resource: Resource, create_new_resource: bool = True
    ) -> None:
        if not isinstance(resource, Resource):
            raise Exception("The resource_set accepts only Resource")

        if isinstance(resource, ResourceListBase):
            raise Exception("ResourceSet does not support nested")

        if not create_new_resource and resource.get_model_id() is None:
            raise Exception(
                "The create_new_resource option was set to False but the resource is not saved in the database"
            )

    @view(
        view_type=ResourcesListView,
        human_name="Resources list",
        short_description="List the resources",
        default_view=True,
    )
    def view_resources_list(self, params: ConfigParams) -> ResourcesListView:
        view_ = ResourcesListView()
        view_.add_resources(self.get_resource_models())
        view_.add_technical_info(
            TechnicalInfo("Number of resources", len(self.get_resources_as_set()))
        )
        return view_

    def __len__(self) -> int:
        return len(self.get_resources_as_set())
