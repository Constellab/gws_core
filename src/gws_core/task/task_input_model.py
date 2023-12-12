# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import List

from peewee import (BooleanField, CharField, CompositeKey, ForeignKeyField,
                    ModelSelect)

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

    experiment: Experiment = ForeignKeyField(
        Experiment, null=True, index=True, on_delete='CASCADE')
    task_model: TaskModel = ForeignKeyField(
        TaskModel, null=True, index=True, on_delete='CASCADE')
    protocol_model: ProtocolModel = ForeignKeyField(
        ProtocolModel, null=True, index=True, on_delete='CASCADE')
    resource_model: ResourceModel = ForeignKeyField(
        ResourceModel, null=True, index=True, on_delete='CASCADE')

    port_name: str = CharField()
    is_interface: bool = BooleanField()

    _table_name = 'gws_task_inputs'

    @classmethod
    def get_by_resource_model(cls, resource_model_id: str) -> ModelSelect:
        return TaskInputModel.select().where(TaskInputModel.resource_model == resource_model_id)

    @classmethod
    def get_by_resource_models(cls, resource_model_ids: List[str]) -> ModelSelect:
        return TaskInputModel.select().where(TaskInputModel.resource_model.in_(resource_model_ids))

    @classmethod
    def get_other_experiments(cls, resource_model_ids: List[str], exclude_experiment_id: str) -> ModelSelect:
        """Method to see if a resource_model is used as input in another experiment
        """
        return TaskInputModel.select().where((TaskInputModel.resource_model.in_(resource_model_ids)) &
                                             (TaskInputModel.experiment != exclude_experiment_id))

    @classmethod
    def get_by_task_model(cls, task_model_id: str) -> ModelSelect:
        return TaskInputModel.select().where(TaskInputModel.task_model == task_model_id)

    @classmethod
    def get_by_task_models(cls, task_model_ids: List[str]) -> ModelSelect:
        return TaskInputModel.select().where(TaskInputModel.task_model.in_(task_model_ids))

    @classmethod
    def get_by_experiment(cls, experiment_id: str) -> ModelSelect:
        return TaskInputModel.select().where(TaskInputModel.experiment == experiment_id)

    @classmethod
    def get_by_experiments(cls, experiment_ids: List[str]) -> ModelSelect:
        return TaskInputModel.select().where(TaskInputModel.experiment.in_(experiment_ids))

    @classmethod
    def delete_by_experiment(cls, experiment_id: str) -> int:
        return TaskInputModel.delete().where(TaskInputModel.experiment == experiment_id).execute()

    @classmethod
    def delete_by_task_ids(cls, task_ids: List[str]) -> int:
        return TaskInputModel.delete().where(TaskInputModel.task_model.in_(task_ids)).execute()

    @classmethod
    def resource_is_used_by_experiment(cls, resource_model_id: str, experiment_ids: List[str]) -> bool:
        """Method to see if a resource_model is used as input in one of the experiments """
        return cls.get_by_resource_model(resource_model_id).where(
            TaskInputModel.experiment.in_(experiment_ids)).exists()

    def save(self, *args, **kwargs) -> 'BaseModel':
        """Use force insert because it is a composite key
        https://stackoverflow.com/questions/30038185/python-peewee-save-doesnt-work-as-expected

        :return: [description]
        :rtype: [type]
        """
        return super().save(*args, force_insert=True, **kwargs)

    class Meta:
        table_name = 'gws_task_inputs'
        primary_key = CompositeKey("task_model", "port_name")
