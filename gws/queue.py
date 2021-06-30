# LICENSE
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import threading
import time
import json

from gws.db.model import Model
from gws.model import User, Experiment
from gws.logger import Error, Info
from peewee import IntegerField, ForeignKeyField, BooleanField

TICK_INTERVAL_SECONDS = 30   # 30 sec

def _queue_tick(tick_interval, verbose, daemon):
    q = Queue()
    if not q.is_active:
        return

    try:
        Queue._tick(verbose)
    finally:
        thread = threading.Timer(tick_interval, _queue_tick, [ tick_interval, verbose, daemon ])    
        thread.daemon = daemon
        thread.start()

class Job(Model):
    """
    Class representing queue job

    :property user: The user who creates the job
    :type user: `gws.model.User`
    :property experiment: The experiment to add to the job
    :type experiment: `gws.model.Expriment`
    """

    user = ForeignKeyField(User, null=True, backref='jobs')
    experiment = ForeignKeyField(Experiment, null=True, backref='jobs')
    _table_name = "gws_queue_job"
    
class Queue(Model):
    """
    Class representing experiment queue

    :property is_active: True is the queue is active; False otherwise. Defaults to False. 
    The queue is automatically set to True on init.
    :type is_active: `bool`
    :property max_length: The maximum length of the queue. Defaults to 10.
    :type max_length: `int`
    """

    is_active = BooleanField(default=False)
    max_length = IntegerField(default=10)
    
    _queue_instance = None
    _is_singleton = True
    _table_name = "gws_queue"
    __is_init = False
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.data.get("jobs"):
            self.data["jobs"] = []
            self.save()
    
    @classmethod
    def init(cls, tick_interval: int=TICK_INTERVAL_SECONDS, verbose=False, daemon=False):
        q = Queue()
        if not cls.__is_init or not q.is_active:
            q.is_active = True
            q.save()
            Info("Queue", "init", "The queue is initialized and active")

            _queue_tick(tick_interval, verbose, daemon)
        
        cls.__is_init = True
        
    @classmethod
    def deinit(cls):
        q = Queue()
        q.is_active = False
        q.save()
    
    # -- A --
    
    @classmethod
    def add(cls, job: Job, auto_start: bool=False):
        if not isinstance(job, Job):
            raise Error("Queue", "add", "Invalid argument. An instance of gws.queue.Jobs is required")
        
        job.save()
        
        q = Queue()
        if job.uri in q.data["jobs"]:
            return
        
        if len(q.data["jobs"]) > q.max_length:
            raise Error("Queue", "add", "The maximum number of jobs is reached")
        
        q.data["jobs"].append(job.uri)
        q.save()
        
        if auto_start:
            if q.is_active:
                #> manally trigger the experiment if possible!
                if not Experiment.count_of_running_experiments():
                    cls._tick()
            else:
                Queue().init()
                
        
    # -- G --
    
    # -- R --
    
    @classmethod
    def remove(self, job: Job):
        if not isinstance(job, Job):
            raise Error("Queue", "add", "Invalid argument. An instance of gws.queue.Job is required")
        
        q = Queue()
        if job.uri in q.data["jobs"]:
            q.data["jobs"].remove(job.uri)
            q.save()
    
    # -- L --
    
    @classmethod
    def length(cls):
        q = Queue()
        return len(q.data["jobs"])
        
    # -- N --
    
    @classmethod
    def next(cls) -> Job:
        q = Queue()
        if not q.data["jobs"]:
            return None
        
        uri = q.data["jobs"][0]
        try:
            return Job.get(Job.uri == uri)
        except:
            # orphan job => discard it from the queue
            cls.__pop_first()
            return cls.next()
    
    # -- P --
    
    @classmethod
    def __pop_first(self):
        q = Queue()
        q.data["jobs"].pop(0)
        q.save()
        
    # -- S --

    # -- T --
    
    @classmethod
    def _tick(cls, verbose=False):
        if verbose:
            Info("Checking experiment queue ...")
            
        job = Queue.next()
        if not job:
            return

        e = job.experiment
        if e.is_finished:
            Queue.__pop_first()
            return
        
        if verbose:
            Info(f"Experiment {e.uri}, is_running = {e.is_running}")
                
        if e.is_running:
            #-> we will test later!
            return
        
        if Experiment.count_of_running_experiments():
            #-> busy: we will test later!
            if verbose:
                Info("The lab is busy! Retry later")
            return
        
        if verbose:
            Info(f"Start experiment {e.uri}, user={job.user.uri}")
            
        e.run_through_cli(user=job.user)
        time.sleep(3)  #-> wait for 3 sec to prevent database lock!

    
    def to_json(self, *args, stringify: bool=False, prettify: bool=False, **kwargs):
        _json = super().to_json(*args, **kwargs)
        _json["jobs"] = []
        for uri in self.data["jobs"]:
            _json["jobs"].append(
                Job.get_by_uri(uri).to_json()
            )
        
        del _json["data"]
        
        if stringify:
            if prettify:
                return json.dumps(_json, indent=4)
            else:
                return json.dumps(_json)
        else:
            return _json
