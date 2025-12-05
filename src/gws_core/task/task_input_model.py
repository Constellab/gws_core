
from peewee import BooleanField, CharField, CompositeKey, ForeignKeyField, ModelSelect

from ..core.model.base_model import BaseModel
from ..protocol.protocol_model import ProtocolModel
from ..resource.resource_model import ResourceModel
from ..scenario.scenario import Scenario
from ..task.task_model import TaskModel


class TaskInputModel(BaseModel):
    """Model use to store where the resource are used as input of tasks

    :param Model: [description]
    :type Model: [type]
    :return: [description]
    :rtype: [type]
    """

    scenario: Scenario = ForeignKeyField(Scenario, null=True, index=True, on_delete="CASCADE")
    task_model: TaskModel = ForeignKeyField(TaskModel, null=True, index=True, on_delete="CASCADE")
    protocol_model: ProtocolModel = ForeignKeyField(
        ProtocolModel, null=True, index=True, on_delete="CASCADE"
    )
    resource_model: ResourceModel = ForeignKeyField(
        ResourceModel, null=True, index=True, on_delete="CASCADE"
    )

    port_name: str = CharField()
    is_interface: bool = BooleanField()

    @classmethod
    def get_by_resource_model(cls, resource_model_id: str) -> ModelSelect:
        return TaskInputModel.select().where(TaskInputModel.resource_model == resource_model_id)

    @classmethod
    def get_by_resource_model_and_task_type(
        cls, resource_model_id: str, task_typing_name: str
    ) -> ModelSelect:
        return (
            TaskInputModel.select()
            .join(TaskModel)
            .where(
                (TaskInputModel.resource_model == resource_model_id)
                & (TaskInputModel.task_model.process_typing_name == task_typing_name)
            )
        )

    @classmethod
    def get_by_resource_models(cls, resource_model_ids: list[str]) -> ModelSelect:
        return TaskInputModel.select().where(TaskInputModel.resource_model.in_(resource_model_ids))

    @classmethod
    def get_other_scenarios(
        cls, resource_model_ids: list[str], exclude_scenario_id: str
    ) -> ModelSelect:
        """Method to see if a resource_model is used as input in another scenario"""
        return TaskInputModel.select().where(
            (TaskInputModel.resource_model.in_(resource_model_ids))
            & (TaskInputModel.scenario != exclude_scenario_id)
        )

    @classmethod
    def get_by_task_model(cls, task_model_id: str) -> ModelSelect:
        return TaskInputModel.select().where(TaskInputModel.task_model == task_model_id)

    @classmethod
    def get_by_task_models(cls, task_model_ids: list[str]) -> ModelSelect:
        return TaskInputModel.select().where(TaskInputModel.task_model.in_(task_model_ids))

    @classmethod
    def get_by_scenario(cls, scenario_id: str) -> ModelSelect:
        return TaskInputModel.select().where(TaskInputModel.scenario == scenario_id)

    @classmethod
    def get_by_scenarios(cls, scenario_ids: list[str]) -> ModelSelect:
        return TaskInputModel.select().where(TaskInputModel.scenario.in_(scenario_ids))

    @classmethod
    def delete_by_task_id(cls, task_id: str) -> int:
        return TaskInputModel.delete().where(TaskInputModel.task_model == task_id).execute()

    @classmethod
    def resource_is_used_by_scenario(cls, resource_model_id: str, scenario_ids: list[str]) -> bool:
        """Method to see if a resource_model is used as input in one of the scenarios"""
        return (
            cls.get_by_resource_model(resource_model_id)
            .where(TaskInputModel.scenario.in_(scenario_ids))
            .exists()
        )

    def save(self, *args, **kwargs) -> "BaseModel":
        """Use force insert because it is a composite key
        https://stackoverflow.com/questions/30038185/python-peewee-save-doesnt-work-as-expected

        :return: [description]
        :rtype: [type]
        """
        return super().save(*args, force_insert=True, **kwargs)

    class Meta:
        table_name = "gws_task_inputs"
        is_table = True
        primary_key = CompositeKey("task_model", "port_name")
