

from typing import List

from peewee import BooleanField, CharField, CompositeKey, ForeignKeyField
from peewee import Model as PeeweeModel
from peewee import ModelDelete, ModelSelect

from ..core.model.base_model import BaseModel
from ..experiment.experiment import Experiment
from ..protocol.protocol_model import ProtocolModel
from ..resource.resource_model import ResourceModel
from ..task.task_model import TaskModel


class TaskInputModel(BaseModel):
    """Model use to store where the resource are used as input of tasks

    :param Model: [description]
    :type Model: [type]
    :return: [description]
    :rtype: [type]
    """

    experiment: Experiment = ForeignKeyField(Experiment, null=True, index=True, on_delete='CASCADE')
    task_model: TaskModel = ForeignKeyField(TaskModel, null=True, index=True, on_delete='CASCADE')
    protocol_model: ProtocolModel = ForeignKeyField(ProtocolModel, null=True, index=True, on_delete='CASCADE')
    resource_model: ResourceModel = ForeignKeyField(ResourceModel, null=True, index=True, on_delete='CASCADE')

    port_name: str = CharField()
    is_interface: bool = BooleanField()

    _table_name = 'gws_task_inputs'

    @classmethod
    def get_by_resource_model(cls, resource_model_id: int) -> ModelSelect:
        return TaskInputModel.select().where(TaskInputModel.resource_model == resource_model_id)

    @classmethod
    def get_other_experiments(cls, resource_model_ids: List[int], exclude_experiment_id: int) -> ModelSelect:
        """Method to see if a resource_model is used as input in another experiment
        """
        return TaskInputModel.select().where(
            TaskInputModel.resource_model.in_(resource_model_ids) & TaskInputModel.experiment != exclude_experiment_id)

    @classmethod
    def get_by_task_model(cls, task_model_id: int) -> ModelSelect:
        return TaskInputModel.select().where(TaskInputModel.task_model == task_model_id)

    @classmethod
    def get_by_experiment(cls, experiment_id: int) -> ModelSelect:
        return TaskInputModel.select().where(TaskInputModel.experiment == experiment_id)

    @classmethod
    def delete_by_experiment(cls, experiment_id: int) -> ModelDelete:
        return TaskInputModel.delete().where(TaskInputModel.task_model == experiment_id)

    def save(self, *args, **kwargs) -> 'BaseModel':
        """Use force insert because it is a composite key
        https://stackoverflow.com/questions/30038185/python-peewee-save-doesnt-work-as-expected

        :return: [description]
        :rtype: [type]
        """
        return super().save(*args, force_insert=True, **kwargs)

    class Meta:
        primary_key = CompositeKey("task_model", "port_name")
