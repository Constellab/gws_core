# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com
from __future__ import annotations

from typing import TYPE_CHECKING, final

from peewee import CharField, IntegerField, ModelSelect

from ..core.exception.exceptions.bad_request_exception import \
    BadRequestException
from ..core.model.model import Model
from ..model.typing_manager import TypingManager
from ..model.typing_register_decorator import TypingDecorator
from ..model.viewable import Viewable

if TYPE_CHECKING:
    from ..experiment.experiment import Experiment
    from ..process.processable_model import ProcessableModel

# Typing names generated for the class Resource
CONST_RESOURCE_TYPING_NAME = "PROCESS.gws_core.Resource"


# Use the typing decorator to avoid circular dependency
@TypingDecorator(unique_name="Resource", object_type="RESOURCE", hide=True)
class Resource(Viewable):
    """
    Resource class.

    :property process: The process that created he resource
    :type process: ProcessableModel
    """

    typing_name = CharField(null=False)

    _process: ProcessableModel = None
    _experiment: Experiment = None
    _table_name = 'gws_resource'

    def __init__(self, *args, process: ProcessableModel = None, experiment: Experiment = None, **kwargs):
        super().__init__(*args, **kwargs)

        # check that the class level property _typing_name is set
        if self._typing_name == CONST_RESOURCE_TYPING_NAME and type(self) != Resource:  # pylint: disable=unidiomatic-typecheck
            raise BadRequestException(
                f"The resource {self.full_classname()} is not decorated with @ResourceDecorator, it can't be instantiate. Please decorate the process class with @ResourceDecorator")

        if self.typing_name is None:
            # set the typing name
            self.typing_name = self._typing_name

        if process:
            self.process = process
        if experiment:
            self.experiment = experiment

    # -- D --

    @classmethod
    def drop_table(cls, *args, **kwargs):
        super().drop_table(*args, **kwargs)
        ProcessResource.drop_table()
        ExperimentResource.drop_table()

    # -- E --

    @property
    def experiment(self):
        """
        Returns the parent experiment
        """

        if not self._experiment:
            try:
                mapping = ExperimentResource.get(
                    (ExperimentResource.resource_id == self.id) &
                    (ExperimentResource.resource_typing_name == self.typing_name)
                )
                self._experiment = mapping.experiment
            except:
                return None

        return self._experiment

    @experiment.setter
    def experiment(self, experiment: Experiment):
        """
        Set the parent experiment
        """

        if self.experiment:
            return

        if not self.id:
            self.save()

        mapping = ExperimentResource(
            experiment_id=experiment.id,
            resource_id=self.id,
            resource_typing_name=self.typing_name,
        )
        mapping.save()
        self._experiment = experiment

    def _export(self, file_path: str, file_format: str = None):
        """
        Export the resource to a repository

        :param file_path: The destination file path
        :type file_path: str
        """

        # @ToDo: ensure that this method is only called by an Exporter

        pass

    # -- G --

    # -- I --

    @classmethod
    def _import(cls, file_path: str, file_format: str = None) -> any:
        """
        Import a resource from a repository. Must be overloaded by the child class.

        :param file_path: The source file path
        :type file_path: str
        :returns: the parsed data
        :rtype any
        """

        # @ToDo: ensure that this method is only called by an Importer

        pass

    # -- J --

    @classmethod
    def _join(cls, *args, **params) -> 'Model':
        """
        Join several resources

        :param params: Joining parameters
        :type params: dict
        """

        # @ToDo: ensure that this method is only called by an Joiner

        pass

    # -- P --

    @property
    def process(self):
        """
        Returns the parent process
        """

        if not self._process:
            try:
                o = ProcessResource.get(
                    (ProcessResource.resource_id == self.id) &
                    (ProcessResource.resource_typing_name == self.typing_name)
                )
                self._process = o.process
            except Exception as _:
                return None

        return self._process

    @process.setter
    def process(self, process: ProcessableModel):
        """
        Set the parent process
        """

        if self.process:
            return

        if not self.id:
            self.save()

        mapping = ProcessResource(
            process_id=process.id,
            processable_typing_name=process.processable_typing_name,
            resource_id=self.id,
            resource_typing_name=self.typing_name,
        )
        mapping.save()
        self._process = process

    # -- R --

    # -- S --

    def _select(self, **params) -> 'Model':
        """
        Select a part of the resource

        :param params: Extraction parameters
        :type params: dict
        """

        # @ToDo: ensure that this method is only called by a Selector
        pass

    @classmethod
    def select_me(cls, *args, **kwargs) -> ModelSelect:
        """
        Select objects by ensuring that the object-type is the same as the current model.
        """

        return cls.select(*args, **kwargs).where(cls.typing_name == cls._typing_name)

    # -- T --
    @final
    def to_json(self, deep: bool = False, **kwargs) -> dict:
        """
        Returns JSON string or dictionnary representation of the model.

        :param stringify: If True, returns a JSON string. Returns a python dictionary otherwise. Defaults to False
        :type stringify: bool
        :param prettify: If True, indent the JSON string. Defaults to False.
        :type prettify: bool
        :return: The representation
        :rtype: dict, str
        """

        _json = super().to_json(deep=deep, **kwargs)
        if self.experiment:
            _json.update({
                "experiment": {"uri": self.experiment.uri},
                "process": {
                    "uri": self.process.uri,
                    "typing_name": self.process.processable_typing_name,
                },
            })

        return _json

    # -- V --


class ExperimentResource(Model):
    """
    ExperimentResource class

    This class manages 1-to-many relationships between experiments and child resources (i.e. resources
    generated from related experiments)

    Mapping: [1](Experiment) ---(generate)---> [*](Resource)

    Because resources are allowed to be stored in different tables (e.g. after model inheritance), this class
    allows to load the related resources from the proper tables.
    """

    # Todo:
    # -----
    # * Try to replace `experiment_id` and `resource_id` columns by foreign keys with `lazy_load=False`

    experiment_id = IntegerField(null=False, index=True)
    resource_id = IntegerField(null=False, index=True)
    resource_typing_name = CharField(null=False, index=True)
    _table_name = "gws_experiment_resource"

    @property
    def resource(self):
        """
        Returns the resource
        """
        return TypingManager.get_object_with_typing_name(self.resource_typing_name, self.resource_id)

    @property
    def experiment(self):
        """
        Returns the experiment
        """

        from ..experiment.experiment import Experiment
        return Experiment.get_by_id(self.experiment_id)

    class Meta:
        indexes = (
            (("experiment_id", "resource_id", "resource_typing_name"), True),
        )


class ProcessResource(Model):
    """
    ProcessResource class

    This class manages 1-to-many relationships between processes and child resources (i.e. resources
    generated by related processes)

    Mapping: [1](ProcessableModel) ---(generate)---> [*](Resource)

    Because resources are allowed to be stored in different tables (e.g. after model inheritance), this class
    allows to load the related processes and resources from the proper tables.
    """

    # @Todo:
    # -----
    # * Try to replace `experiment_id` and `resource_id` columns by foreign keys with `lazy_load=False`
    # Do we need the typings ? We do we do if the typing name changed

    process_id = IntegerField(null=False, index=True)
    processable_typing_name = CharField(null=False, index=True)
    resource_id = IntegerField(null=False, index=True)
    resource_typing_name = CharField(null=False, index=True)
    _table_name = "gws_process_resource"

    @property
    def resource(self):
        """
        Returns the resource
        """
        return TypingManager.get_object_with_typing_name(self.resource_typing_name, self.resource_id)

    @property
    def process(self):
        """
        Returns the process
        """
        return TypingManager.get_object_with_typing_name(self.processable_typing_name, self.process_id)

    class Meta:
        indexes = (
            (("process_id", "processable_typing_name",
             "resource_id", "resource_typing_name"), True),
        )
