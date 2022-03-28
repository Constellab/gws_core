# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com
from __future__ import annotations

from typing import TYPE_CHECKING, List, Set

from gws_core.config.config_types import ConfigParams
from gws_core.impl.view.resources_list_view import ResourcesListView
from gws_core.resource.r_field import ListRField
from gws_core.resource.view_decorator import view

from .resource import Resource
from .resource_decorator import resource_decorator

if TYPE_CHECKING:
    from gws_core.resource.resource_model import ResourceModel


@resource_decorator(unique_name="ResourceSet", human_name="Resource set",
                    short_description="A set of resources")
class ResourceSet(Resource):
    """Resource to manage a set of resources

    :param Resource: _description_
    :type Resource: _type_
    :raises Exception: _description_
    :raises Exception: _description_
    :return: _description_
    :rtype: _type_
    """

    _resource_ids: List[str] = ListRField()

    _resources: Set[Resource] = None

    @property
    def resources(self) -> Set[Resource]:
        if self._resources is None:
            self._resources = self._load_resources()

        return self._resources

    @resources.setter
    def resources(self, resources: Set[Resource]) -> None:
        if not isinstance(resources, set):
            raise Exception('The resource_set only takes set of resources')
        self._resource_ids = []
        self._resources = set()
        for resource in resources:
            self.add_resource(resource)

    def add_resource(self, resource: Resource) -> None:
        if not isinstance(resource, Resource):
            raise Exception('The resource_set only takes set of resources')

        if isinstance(resource, ResourceSet):
            raise Exception('ResourceSet does not support nested')

        if self._resources is None:
            self._resources = set()

        if self._resource_ids is None:
            self._resource_ids = []

        if resource._model_id is not None:
            self._resource_ids.append(resource._model_id)

        self._resources.add(resource)

    def _load_resources(self,) -> Set[Resource]:
        if not resource_ids:
            return set()

        resource_models: List[ResourceModel] = list(ResourceModel.select().where(ResourceModel.id.in_(resource_ids)))

        resources: Set[Resource] = set()
        for resource_model in resource_models:
            resources.add(resource_model.get_resource())
        return resources

    def _get_resource_models(self) -> List[ResourceModel]:
        from .resource_model import ResourceModel
        return list(ResourceModel.select().where(ResourceModel.id.in_(self._resource_ids)))

    @view(view_type=ResourcesListView, human_name='Resources list',
          short_description='List the resources', default_view=True)
    def view_resources_list(self, params: ConfigParams) -> ResourcesListView:
        """
        View the table as Venn diagram
        """
        view = ResourcesListView()
        view.add_resources(self._get_resource_models())
        return view
