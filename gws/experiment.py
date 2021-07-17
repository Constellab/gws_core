# LICENSE
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import os
import json
import time
import subprocess

from peewee import  IntegerField, FloatField, BooleanField, ForeignKeyField, ManyToManyField
from .viewable import Viewable
from .study import Study
from .user import User
from .event import EventListener
from .logger import Error, Info
from .protocol import Protocol
from .settings import Settings

class Experiment(Viewable):
    """
    Experiment class.
    
    :property study: The study of the experiment
    :type study: `gws.study.Study`
    :property protocol: The the protocol of the experiment
    :type protocol: `gws.protocol.Protocol`
    :property created_by: The user who created the experiment. This user may be different from the user who runs the experiment.
    :type created_by: `gws.user.User`
    :property score: The score of the experiment
    :type score: `float`
    :property is_validated: True if the experiment is validated, False otherwise. Defaults to False.
    :type is_validated: `bool`
    """

    study = ForeignKeyField(Study, null=True, index=True, backref='experiments')
    protocol = ForeignKeyField(Protocol, null=True, index=True, backref='+')
    created_by = ForeignKeyField(User, null=True, index=True, backref='created_experiments')
    score = FloatField(null=True, index=True)
    is_validated = BooleanField(default=False, index=True)

    _is_running = BooleanField(default=False, index=True)
    _is_finished = BooleanField(default=False, index=True)
    _is_success = BooleanField(default=False, index=True)
    _event_listener: EventListener = None
    _table_name = 'gws_experiment'

    def __init__(self, *args, user:User=None, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.id:
            self.data["pid"] = 0
            if user is None:
                try:
                    from .service.user_service import UserService
                    user = UserService.get_current_user()
                except Exception as err:
                    raise Error("gws.experiment.Experiment", "__init__", "An user is required") from err
                    
            if isinstance(user, User):
                if not user.is_authenticated:
                    raise Error("gws.experiment.Experiment", "__init__", "An authenticated user is required")
                
                self.created_by = user
            else:
                raise Error("gws.experiment.Experiment", "__init__", "The user must be an instance of User")
            
            if not self.save():
                raise Error("gws.experiment.Experiment", "__init__", "Cannot create experiment")
                
            # attach the protocol
            protocol = kwargs.get("protocol")
            if protocol is None:
                from .protocol import Protocol
                protocol = Protocol(user=user)
            
            protocol.set_experiment(self)
            self.protocol = protocol
            self.save()
            
        else:
            pass
        
        self._event_listener = EventListener()
        
    # -- A --
    
    def add_report(self, report: 'Report'):
        report.experiment = self

    def archive(self, tf:bool, archive_resources=True) -> bool:
        """
        Archive the experiment
        """

        from .activity import Activity
        if self.is_archived == tf:
            return True
        with self._db_manager.db.atomic() as transaction:
            Activity.add(
                Activity.ARCHIVE,
                object_type = self.full_classname(),
                object_uri = self.uri
            )
            if not self.protocol.archive(tf, archive_resources=archive_resources):
                transaction.rollback()
                return False
            status = super().archive(tf)
            if not status:
                transaction.rollback()
            return status
      
    # -- C --
        
    @classmethod
    def count_of_running_experiments(cls) -> int:
        """ 
        Returns the count of experiment in progress

        :return: The count of experiment in progress
        :rtype: `int`
        """
        
        return Experiment.select().where(Experiment.is_running == True).count()
    
    # -- G --
    
    def get_title(self) -> str:
        """
        Get the title of the experiment. The title is same as the title of the protocol.

        :rtype: `str`
        """

        return self.data.get("title", "")

    def get_description(self) -> str:
        """
        Get the description of the experiment. The description is same as the title of the protocol

        :rtype: `str`
        """

        return self.data.get("description", "")

    # -- I --
    
    @property
    def is_finished(self) -> bool:
        if not self.id:
            return False
        
        e = Experiment.get_by_id(self.id)
        return e._is_finished
    
    @property
    def is_running(self) -> bool:
        if not self.id:
            return False
        
        e = Experiment.get_by_id(self.id)
        return e._is_running
    
    @property
    def is_draft(self) -> bool:
        """ 
        Returns True if the experiment is a draft, i.e. has nether been run and is not validated. False otherwise.

        :return: True if the experiment not running nor finished
        :rtype: `bool`
        """
        
        return (not self.is_validated) and (not self.is_running) and (not self.is_finished)

    @property
    def is_pid_alive(self) -> bool:
        if not self.pid:
            raise Error("Experiment", "is_pid_alive", f"No such process found")
        
        try:
            sproc = SysProc.from_pip(self.pid)
        except:
            raise Error("Experiment", "is_pid_alive", f"No such process found or its access is denied (pid = {self.pid})")
            
        sproc = SysProc.from_pip(self.pid)
        return sproc.is_alive()
    
    # -- J --

    # -- K --
    
    async def kill_pid(self):
        """ 
        Kill the experiment if it is running. 
        
        This is only possible if the experiment has been started through the cli. 
        """
        
        from .activity import Activity
        from .service.http_service import HTTPService
        
        if not HTTPService.is_http_context():
            raise Error("Experiment", "kill_pid", f"The user must be in http context")
            
        if self.pip:
            try:
                sproc = SysProc.from_pip(self.pid)
            except:
                raise Error("Experiment", "is_pid_alive", f"No such process found or its access is denied (pid = {self.pid})")
            
        try:
            sproc.terminate()
            sproc.wait()
        except:
            raise Error("Experiment", "kill", f"Cannot kill pid {self.pid}.")
        
        Activity.add(
            Activity.STOP,
            object_type = self.full_classname(),
            object_uri = self.uri
        )

        # Gracefully stop the experiment and exit!
        message = f"Experiment manullay stopped by a user."
        self.protocol.progress_bar.stop(message)
        self.data["pid"] = 0
        self._is_running = False
        self._is_finished = True
        self._is_success = False
        self.save()
            
    # -- O --

    def on_end(self, call_back: callable):
        self._event_listener.add("end", call_back)
    
    def on_start(self, call_back: callable):
        self._event_listener.add("start", call_back)
        
    # -- P --
    
    @property
    def pid(self) -> int:
        if not "pid" in self.data:
            return 0
        
        return self.data["pid"]
    
    @property
    def processes(self):
        if not self.id:
            return []
        from .process import Process
        return Process.select().where(Process.experiment_id == self.id)
    
    # -- R --

    @property 
    def resources(self):
        from .resource import ExperimentResource
        Qrel = ExperimentResource.select().where(ExperimentResource.experiment_id == self.id)
        Q = []
        for o in Qrel:
            Q.append(o.resource)
            
        return Q
    
    def reset(self) -> bool:
        """ 
        Reset the experiment.

        :return: True if it is reset, False otherwise
        :rtype: `bool`
        """
        
        if self.is_validated or self.is_running:
            return False

        if self.is_finished:
            with self._db_manager.db.atomic() as transaction:
                if self.protocol:
                    if not self.protocol._reset():
                        transaction.rollback()
                        return False

                self._is_running = False
                self._is_finished = False
                self._is_success = False
                self.score = None
                status = self.save()

                if not status:
                    transaction.rollback()
                
                return status
        else:
            return True

    def run_through_cli(self, *, user=None):
        """ 
        Run an experiment in a non-blocking way through the cli.

        :param user: The user who is running the experiment. If not provided, the system will try the get the currently authenticated user
        :type user: `gws.user.User`
        """

        from .system import SysProc
        from .service.user_service import UserService
        
        settings = Settings.retrieve()
        cwd_dir = settings.get_cwd()
        
        if not user:
            try:
                user = UserService.get_current_user()
            except:
                raise Error("gws.experiment.Experiment", "run_through_cli", "A user is required")
            
            if not user.is_authenticated:
                raise Error("gws.experiment.Experiment", "run_through_cli", "An authenticated user is required")
                    
        cmd = [
            "python3", 
             os.path.join(cwd_dir, "manage.py"), 
             "--cli", 
             "gws.cli.run_experiment",
             "--experiment-uri", self.uri,
             "--user-uri", user.uri
        ]
         
        if settings.is_test:
            cmd.append("--cli_test")

        cmd.append("--runmode")
        if settings.is_prod:
            cmd.append("prod")
        else:
            cmd.append("dev")
        
        Info("gws.experiment.Experiment", "run_through_cli", str(cmd))

        sproc = SysProc.popen(cmd, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
        self.data["pid"] = sproc.pid
        self.save()
        
    async def run(self, *, user=None, wait_response=False):
        """ 
        Run the experiment

        :param user: The user who is running the experiment. If not provided, the system will try the get the currently authenticated user
        :type user: `gws.user.User`
        :param wait_response: True to wait the response. False otherwise.
        :type wait_response: `bool`
        """
        
        if self.is_running or self.is_finished:
            return
        
        if wait_response:
            await self.__run(user=user)
        else:
            from .service.http_service import HTTPService
            if HTTPService.is_http_context():
                # run the experiment throug the cli to prevent blocking HTTP requests
                self.run_through_cli(user=user)
            else:
                await self.__run(user=user)
        
    async def __run(self, * ,user: User=None):
        """ 
        Run the experiment

        :param user: The user who is running the experiment. If not provided, the system will try the get the currently authenticated user
        :type user: `gws.user.User`
        """
        
        from .activity import Activity
        from .service.user_service import UserService
        
        if not user:
            try:
                user: User = UserService.get_current_user()
            except:
                raise Error("gws.experiment.Experiment", "run", "A user is required")

            if not user.is_authenticated:
                    raise Error("gws.experiment.Experiment", "run", "A authenticated user is required")
        
        if self.protocol._allowed_user == self.USER_ADMIN:
                if not user.is_admin:
                    raise Error("gws.experiment.Experiment", "run", f"Only admin user can run protocol")

        for proc in self.protocol.processes.values():
            if proc._allowed_user == self.USER_ADMIN:
                if not user.is_admin:
                    raise Error("gws.experiment.Experiment", "run", f"Only admin user can run process '{proc.type}'")

        if self.is_archived:
            raise Error("gws.experiment.Experiment", "run", f"The experiment is archived")

        if self.is_validated:
            raise Error("gws.experiment.Experiment", "run", f"The experiment is validated")

        Activity.add(
            Activity.START,
            object_type = self.full_classname(),
            object_uri = self.uri,
            user=user
        )

        try:
            self.protocol.set_experiment(self)
            self.data["pid"] = 0
            self._is_running = True
            self._is_finished = False
            self.save()

            if self._event_listener.exists("start"):
                self._event_listener.sync_call("start", self)
                await self._event_listener.async_call("start", self)

            await self.protocol._run()

            if self._event_listener.exists("end"):
                self._event_listener.sync_call("end", self)
                await self._event_listener.async_call("end", self)

            self.data["pid"] = 0
            self._is_running = False
            self._is_finished = True
            self._is_success = True
            self.save()
        except Exception as err:
            time.sleep(3)  #-> wait for 3 sec to prevent database lock!

            # Gracefully stop the experiment and exit!
            message = f"An error occured. Exception: {err}"
            self.protocol.progress_bar.stop(message)
            self.data["pid"] = 0
            self._is_running = False
            self._is_finished = True
            self._is_success = False
            self.save()
            raise Error("gws.experiment.Experiment", "run", message) from err
                
    # -- S --

    def set_title(self, title:str) -> str:
        """
        Set the title of the experiment. This title is set to the protocol.

        :param title: The title
        :type title: `str`
        """

        self.data["title"] = title

    def set_description(self, description:str) -> str:
        """
        Get the description of the experiment. This description is set to the protocol.

        :param description: The description
        :type description: `str`
        """

        self.data["description"] = description

    def save(self, *args, **kwargs):
        from .activity import Activity
        with self._db_manager.db.atomic() as transaction:
            if not self.is_saved():
                Activity.add(
                    Activity.CREATE,
                    object_type = self.full_classname(),
                    object_uri = self.uri
                )
            status = super().save(*args, **kwargs)
            if not status:
                transaction.rollback()
            return status

    # -- T --
    
    def to_json(self, *, stringify: bool=False, prettify: bool=False, **kwargs) -> (str, dict, ):
        """
        Returns JSON string or dictionnary representation of the experiment.
        
        :param stringify: If True, returns a JSON string. Returns a python dictionary otherwise. Defaults to False
        :type stringify: bool
        :param prettify: If True, indent the JSON string. Defaults to False.
        :type prettify: bool
        :return: The representation
        :rtype: dict, str
        """
        
        _json = super().to_json(**kwargs)
        _json.update({
            "study": {"uri": self.study.uri},
            "protocol": {
                "uri": self.protocol.uri,
                "type": self.protocol.type
            },
            "is_draft": self.is_draft,
            "is_running": self.is_running,
            "is_finished": self.is_finished,
            "is_success": self._is_success
        })
        
        if stringify:
            if prettify:
                return json.dumps(_json, indent=4)
            else:
                return json.dumps(_json)
        else:
            return _json   
    
    def validate(self, user: User):
        """
        Validate the experiment
        
        :param user: The user who validate the experiment
        :type user: `gws.user.User`
        """
        
        from .activity import Activity
        if self.is_validated:
            return
        if not self.is_finished:
            return
        with self._db_manager.db.atomic() as transaction:
            self.is_validated = True
            if self.save():
                Activity.add(
                    Activity.VALIDATE,
                    object_type = self.full_classname(),
                    object_uri = self.uri
                )

    # -- V --