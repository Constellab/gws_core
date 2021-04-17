# LICENSE
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from gws.model import Model, User, Experiment
from peewee import IntegerField, ForeignKeyField
import threading
import time

TICK_INTERVAL_SECONDS = 60   # 1 min

def _queue_tick(tick_interval, verbose, daemon):    
    try:
        Queue._tick(verbose)
    except:
        pass
    
    t = threading.Timer(tick_interval, _queue_tick, [ tick_interval, verbose, daemon ])    
    t.daemon = daemon
    t.start()

class Job(Model):
    user = ForeignKeyField(User, null=True, backref='jobs')
    experiment = ForeignKeyField(Experiment, null=True, backref='jobs')
    _table_name = "gws_queue_job"
    
class Queue(Model):
    max_number_of_jobs = IntegerField(default=10)
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
    def init(cls, tick_interval: int=TICK_INTERVAL_SECONDS, verbose=False, daemon=True):
        if not cls.__is_init:
            cls.__is_init = True
            _queue_tick(tick_interval, verbose, daemon)
        
    # -- A --
    
    @classmethod
    def add(cls, job: Job, start: bool=False):
        if not isinstance(job, Job):
            raise Error("Queue", "add", "Invalid argument. An instance of gws.queue.Jobs is required")
        
        job.save()
        
        q = Queue()
        if job.uri in q.data["jobs"]:
            return
        
        if len(q.data["jobs"]) > q.max_number_of_jobs:
            raise Error("Queue", "add", "Max number of jobs is reached")
        
        q.data["jobs"].append(job.uri)
        q.save()
        
        if start:
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
        if not cls.data["jobs"]:
            return None
        
        q = Queue()
        uri = q.data["jobs"][0]  

        try:
            return Job.get(Job.uri == uri)
        except:
            return None
    
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
            print("Checking experiment queue ...")
            
        job = Queue.next()
        if not job:
            return

        e = job.experiment
        if e.is_finished:
            Queue.__pop_first()
            return
        
        if e.is_running:
            #-> we will test later!
            return
        
        e.run_through_cli(user=job.user)
        time.sleep(3)  #-> wait for 3 sec to prevent database lock!