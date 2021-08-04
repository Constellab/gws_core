# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import os
import subprocess
from typing import Union

from peewee import ModelSelect

from ..core.classes.paginator import Paginator
from ..core.exception.exceptions import BadRequestException, NotFoundException
from ..core.model.sys_proc import SysProc
from ..core.service.base_service import BaseService
from ..core.utils.http_helper import HTTPHelper
from ..core.utils.logger import Logger
from ..core.utils.settings import Settings
from ..protocol.protocol import Protocol
from ..study.study import Study
from ..user.activity import Activity
from ..user.activity_service import ActivityService
from ..user.current_user_service import CurrentUserService
from ..user.user import User
from .experiment import Experiment
from .experiment_dto import ExperimentDTO


class ExperimentService(BaseService):

    # -- C --

    @classmethod
    def create_experiment(cls, experiment: ExperimentDTO) -> Experiment:
        try:
            study = Study.get_default_instance()
            proto = Protocol()
            e = proto.create_experiment(
                user=CurrentUserService.get_and_check_current_user(),
                study=study
            )

            if experiment.title:
                e.set_title(experiment.title)

            if experiment.description:
                e.set_description(experiment.description)

            e.save()
            return e
        except Exception as err:
            raise BadRequestException(
                detail=f"Cannot create the experiment.") from err

    # -- F --

    @classmethod
    def fetch_experiment(cls, uri=None) -> Union[Experiment, dict]:
        try:
            e = Experiment.get(Experiment.uri == uri)
        except Exception as err:
            raise NotFoundException(
                detail=f"No experiment found with uri '{uri}'") from err

        return e

    @classmethod
    def fetch_experiment_list(cls,
                              page: int = 1,
                              number_of_items_per_page: int = 20) -> Paginator:

        number_of_items_per_page = cls.get_number_of_item_per_page(
            number_of_items_per_page)

        query = Experiment.select().order_by(Experiment.creation_datetime.desc())

        paginator = Paginator(
            query, page=page, number_of_items_per_page=number_of_items_per_page)

        return paginator

    @classmethod
    def search(cls,
               search_text: str,
               page: int = 1,
               number_of_items_per_page: int = 20,
               as_json: bool = False) -> Paginator:

        number_of_items_per_page = cls.get_number_of_item_per_page(
            number_of_items_per_page)

        query: ModelSelect = Experiment.search(search_text)
        result = []
        for o in query:
            if as_json:
                result.append(o.get_related().to_json(shallow=True))
            else:
                result.append(o.get_related())

        paginator = Paginator(
            query, page=page, number_of_items_per_page=number_of_items_per_page)
        return {
            'data': result,
            'paginator': paginator.paginator_dict()
        }

    # -- S --

    @classmethod
    async def stop_experiment(cls, uri) -> Experiment:
        experiment: Experiment = None

        try:
            experiment = Experiment.get(Experiment.uri == uri)
        except Exception as err:
            raise BadRequestException(
                detail=f"Experiment '{uri}' not found") from err

        experiment.check_is_stopable()

        try:
            experiment.kill_pid()
            return experiment
        except Exception as err:
            raise BadRequestException(
                detail=f"Cannot kill experiment '{uri}'") from err

    # -- U --

    @classmethod
    def update_experiment(cls, uri, experiment: ExperimentDTO) -> Experiment:
        try:
            e = Experiment.get(Experiment.uri == uri)
            if not e.is_draft:
                raise BadRequestException(
                    detail=f"Experiment '{uri}' is not a draft")

            if experiment.graph:
                proto = e.protocol
                proto._build_from_dump(graph=experiment.graph, rebuild=True)
                proto.save()

            if experiment.title:
                e.set_title(experiment.title)

            if experiment.description:
                e.set_description(experiment.description)

            e.save()
            return e
        except Exception as err:
            raise BadRequestException(
                detail="Cannot update experiment") from err

    # -- V --

    @classmethod
    def validate_experiment(cls, uri) -> Experiment:
        experiment: Experiment = None
        try:
            experiment = Experiment.get(Experiment.uri == uri)
        except Exception as err:
            raise NotFoundException(
                detail=f"Experiment '{uri}' not found") from err

        try:
            experiment.validate(
                user=CurrentUserService.get_and_check_current_user())
            return experiment
        except Exception as err:
            raise NotFoundException(
                detail=f"Cannot validate experiment '{uri}'") from err

    @classmethod
    async def run_experiment(cls, experiment_uri: str, user: User = None, wait_response=False) -> Experiment:
        """
        Run the experiment
        :param experiment_uri: The uri of the experiment to run
        :type experiment_uri: `str`
        :param user: The user who is running the experiment. If not provided, the system will try the get the currently authenticated user
        :type user: `gws.user.User`
        :param wait_response: True to wait the response. False otherwise.
        :type wait_response: `bool`
        """

        experiment: Experiment = None
        try:
            experiment = Experiment.get(
                Experiment.uri == experiment_uri)
        except Exception as err:
            raise BadRequestException(
                f"No experiment found with uri {experiment_uri}. Error: {err}") from err

        if experiment.is_running:
            raise BadRequestException("The experiment is already running")
        elif experiment.is_finished:
            raise BadRequestException("The experiment is already finished")
        else:
            try:
                if wait_response:
                    await cls._run_experiment(experiment=experiment, user=user)
                else:
                    if HTTPHelper.is_http_context():
                        # run the experiment throug the cli to prevent blocking HTTP requests
                        cls.run_through_cli(experiment=experiment, user=user)
                    else:
                        await cls._run_experiment(experiment=experiment, user=user)
            except Exception as err:
                Logger.log_exception_stack_trace()
                raise BadRequestException(
                    f"An error occured. Error: {err}") from err

    @classmethod
    async def _run_experiment(cls, experiment: Experiment, user: User = None) -> Experiment:
        """
        Run the experiment

        :param user: The user who is running the experiment. If not provided, the system will try the get the currently authenticated user
        :type user: `gws.user.User`
        """
        # check user
        if not user:
            try:
                user: User = CurrentUserService.get_and_check_current_user()
            except:
                raise BadRequestException("A user is required")

        # check user privilege
        experiment.check_user_privilege(user)

        # check experiment status
        experiment.check_is_runnable()

        ActivityService.add(
            Activity.START,
            object_type=experiment.full_classname(),
            object_uri=experiment.uri,
            user=user
        )

        try:
            await experiment.mark_as_started()

            await experiment.protocol._run()

            await experiment.mark_as_success()
        except Exception as err:
            # time.sleep(3)  # -> wait for 3 sec to prevent database lock!

            # Gracefully stop the experiment and exit!
            message = f"An error occured. Exception: {err}"
            experiment.mark_as_error(message)
            raise err

    @classmethod
    def run_through_cli(cls, *, experiment: Experiment, user=None):
        """
        Run an experiment in a non-blocking way through the cli.

        :param user: The user who is running the experiment. If not provided, the system will try the get the currently authenticated user
        :type user: `gws.user.User`
        """

        settings: Settings = Settings.retrieve()
        cwd_dir = settings.get_cwd()

        # check user
        if not user:
            try:
                user = CurrentUserService.get_and_check_current_user()
            except:
                raise BadRequestException("A user is required")
            if not user.is_authenticated:
                raise BadRequestException("An authenticated user is required")

         # check user privilege
        experiment.check_user_privilege(user)

        # check experiment status
        experiment.check_is_runnable()

        cmd = [
            "python3",
            os.path.join(cwd_dir, "manage.py"),
            "--cli",
            "gws_core.cli.run_experiment",
            "--experiment-uri", experiment.uri,
            "--user-uri", user.uri
        ]

        if settings.is_test:
            cmd.append("--cli_test")

        cmd.append("--runmode")
        if settings.is_prod:
            cmd.append("prod")
        else:
            cmd.append("dev")

        Logger.info(f"gws.experiment.Experiment run_through_cli {str(cmd)}")
        sproc = SysProc.popen(
            cmd, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
        experiment.data["pid"] = sproc.pid
        experiment.save()

    @classmethod
    def count_of_running_experiments(cls) -> int:
        """
        Returns the count of experiment in progress

        :return: The count of experiment in progress
        :rtype: `int`
        """

        return Experiment.count_of_running_experiments()
