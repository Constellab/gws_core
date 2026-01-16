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

    # list the resource model ids that are constant (the system doesn't create new resources on save)
    __constant_resource_uid__: set[str] | None = None

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

    def _mark_resource_as_constant(
        self,
        resource: Resource,
    ) -> None:
        """Mark the resource as constant, so the system will not create a new resource on save"""
        constant_resource_uids = self.__get_constant_resource_uid__()
        constant_resource_uids.add(resource.uid)

    def __resource_is_constant__(self, resource: Resource) -> bool:
        """return true if the resource is constant and was create before
        a task that generated this resource set
        """
        return resource.uid in self.__get_constant_resource_uid__()

    def __get_constant_resource_uid__(self) -> set[str]:
        """Add the resource uid to the constant resource uid set"""
        if self.__constant_resource_uid__ is None:
            self.__constant_resource_uid__ = set()

            # load existing constant resource uids
            resources = self.get_resources_as_set()
            for resource in resources:
                self.__constant_resource_uid__.add(resource.uid)
        return self.__constant_resource_uid__

    def _get_resource_by_model_id(self, resource_model_id: str) -> Resource:
        if resource_model_id not in self.get_resource_model_ids():
            raise Exception(f"The resource with id {resource_model_id} is not in the resource list")

        from ..resource_model import ResourceModel  # noqa: PLC0415

        return ResourceModel.get_by_id_and_check(resource_model_id).get_resource()

    @abstractmethod
    def __set_r_field__(self, saved_resources: dict[str, Resource]) -> None:
        """This method is called before the save of this resource but after the save of the
        child resources. Set the r_field of this resource with the ids of the child

        :param saved_resources: dict where key is the resource uid and value is the saved resource
        :type saved_resources: Dict[str, Resource]
        :raises NotImplementedError: _description_
        """
        raise NotImplementedError()

    @final
    def save_new_children_resources(
        self,
        resource_origin: ResourceOrigin,
        scenario: Scenario | None = None,
        task_model: TaskModel | None = None,
        port_name: str | None = None,
    ) -> list[ResourceModel]:
        from ..resource_model import ResourceModel  # noqa: PLC0415

        new_children_resources: list[ResourceModel] = []

        new_resources: dict[str, Resource] = {}
        for resource in self.get_resources_as_set():
            if self.__resource_is_constant__(resource):
                if resource.get_model_id() is None:
                    raise Exception(
                        f"The resource {resource.name or resource.uid} is marked as constant resource in the resource list, "
                        "but the resource is not saved in the database. If you want to add a new resource, set create_new_resource to True. "
                        "If you want to add an existing resource, use an existing resource from the task inputs."
                    )

                new_resources[resource.uid] = resource
            else:
                # create and save the resource model from the resource
                resource_model = ResourceModel.save_from_resource(
                    resource,
                    origin=resource_origin,
                    scenario=scenario,
                    task_model=task_model,
                    port_name=port_name,
                )
                new_resources[resource.uid] = resource_model.get_resource()
                new_children_resources.append(resource_model)
        self.__set_r_field__(new_resources)
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
        from ..resource_model import ResourceModel  # noqa: PLC0415

        resource_ids = list(self.get_resource_model_ids())

        if not resource_ids:
            return []

        return list(
            ResourceModel.select()
            .where(ResourceModel.id.in_(resource_ids))
            .order_by(ResourceModel.name)
        )

    def _check_resource_before_add(
        self,
        resource: Resource,
    ) -> None:
        if not isinstance(resource, Resource):
            raise Exception("The resource_set accepts only Resource")

        if isinstance(resource, ResourceListBase):
            raise Exception("ResourceSet does not support nested")

        # force the load of constant resource uids
        self.__get_constant_resource_uid__()

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
