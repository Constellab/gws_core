# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from peewee import CharField, IntegerField, ModelSelect

from ..core.model.model import Model


class TaskResource(Model):
    """
    TaskResource class

    This class manages 1-to-many relationships between tasks and child resources (i.e. resources
    generated by related tasks)

    Mapping: [1](TaskModel) ---(generate)---> [*](Resource)

    Because resources are allowed to be stored in different tables (e.g. after model inheritance), this class
    allows to load the related tasks and resources from the proper tables.
    """

    # @Todo:
    # -----
    # * Try to replace `experiment_id` and `resource_id` columns by foreign keys with `lazy_load=False`
    # Do we need the typings ? We do we do if the typing name changed

    task_model_id = IntegerField(null=False, index=True)
    resource_model_id = IntegerField(null=False, index=True)
    resource_model_typing_name = CharField(null=False, index=True)
    _table_name = "gws_task_resource"

    @property
    def resource(self):
        """
        Returns the resource
        """
        from .resource_model import ResourceModel
        return ResourceModel.get_by_id(self.resource_model_id)

    @property
    def task_model(self):
        """
        Returns the task model
        """
        from ..task.task_model import TaskModel
        return TaskModel.get_by_id(self.task_model_id)

    @classmethod
    def get_by_id_and_tying_name(cls, resource_id: int, resource_model_typing_name: str) -> ModelSelect:
        TaskResource.get(
            (TaskResource.resource_model_id == resource_id) &
            (TaskResource.resource_model_typing_name == resource_model_typing_name))

    class Meta:
        indexes = (
            (("task_model_id", "resource_model_id", "resource_model_typing_name"), True),
        )