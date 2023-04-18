# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import List, Optional

from pydantic import BaseModel

from gws_core.experiment.experiment import Experiment
from gws_core.progress_bar.progress_bar import ProgressBarMessage


# DTO to create/update an experiment
class ExperimentDTO(BaseModel):
    project_id: Optional[str] = None
    title: str = None


class RunningProcessInfo(BaseModel):
    id: str
    title: str
    last_message: ProgressBarMessage
    progression: float


class RunningExperimentInfo(BaseModel):
    id: str
    title: str = None
    project: Optional[dict]
    running_tasks: List[RunningProcessInfo] = []

    def add_running_task(self, task: RunningProcessInfo) -> None:
        self.running_tasks.append(task)

    @classmethod
    def from_experiment(cls, experiment: Experiment) -> 'RunningExperimentInfo':
        project = None
        if experiment.project:
            project = {
                'id': experiment.project.id,
                'title': experiment.project.title
            }
        running_experiment_info = RunningExperimentInfo(id=experiment.id,
                                                        title=experiment.title,
                                                        project=project,
                                                        running_tasks=[])
        return running_experiment_info
