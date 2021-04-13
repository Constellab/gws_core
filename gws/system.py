# LICENSE
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import psutil
import subprocess
from subprocess import DEVNULL
from gws.logger import Error
from gws.model import Model
import threading

from peewee import FloatField

TICK_INTERVAL_SECONDS = 60*5   # 5 min

def _system_monitor_tick():
    Monitor._tick()
    t = threading.Timer(TICK_INTERVAL_SECONDS, _system_monitor_tick)
    t.daemon=True
    t.start()

class Monitor(Model):
    cpu_count = FloatField()
    cpu_percent = FloatField(index=True)
    
    disk_total = FloatField()
    disk_usage_used = FloatField(index=True)
    disk_usage_free = FloatField(index=True)
    disk_usage_percent = FloatField(index=True)
    
    swap_memory_total = FloatField(index=True)
    swap_memory_used = FloatField(index=True)
    swap_memory_free = FloatField(index=True)
    swap_memory_percent = FloatField(index=True)
    
    net_io_bytes_sent = FloatField(index=True)
    net_io_bytes_recv = FloatField(index=True)
    
    _table_name = 'gws_monitor'
    __is_init = False
    
 
    @classmethod
    def init(cls):
        if not cls.__is_init:
            cls.__is_init = True
            _system_monitor_tick()
    
    @classmethod
    def get_last(cls):
        return Monitor.select().order_by(Monitor.id.desc()).get()
    
    @classmethod
    def _tick(cls):
        try:
            monitor = Monitor()

            disk = psutil.disk_usage("/")
            swap = psutil.swap_memory()
            iobytes = psutil.net_io_counters()

            monitor.cpu_count = psutil.cpu_count()
            monitor.cpu_percent = psutil.cpu_percent(interval=None)
            monitor.data["all_cpu_percent"] = psutil.cpu_percent(interval=None, percpu=True)
            
            monitor.disk_total = disk.total
            monitor.disk_usage_used = disk.used
            monitor.disk_usage_free = disk.free
            monitor.disk_usage_percent = disk.percent

            monitor.swap_memory_total = swap.total
            monitor.swap_memory_used = swap.used
            monitor.swap_memory_free = swap.free
            monitor.swap_memory_percent = swap.percent
            
            monitor.net_io_bytes_sent = iobytes.bytes_sent
            monitor.net_io_bytes_recv = iobytes.bytes_recv

            monitor.save()
        except:
            pass
        
class SysProc:
    _ps = None
    
    @staticmethod
    def from_pid(pid):
        proc = SysProc()
        proc._ps = psutil.Process(pid)
        return proc
    
    def is_alive(self):
        return psutil.pid_exists(self.pid)
    
    def kill(self):
        if self.is_alive():
            self._ps.kill()
    
    @property
    def pid(self):
        if self._ps:
            return self._ps.pid
        else:
            return 0
    
    @classmethod
    def popen(cls, cmd, *args, **kwargs) -> 'SysProc':
        try:
            proc = SysProc()
            proc._ps = psutil.Popen(cmd, *args, **kwargs)
            return proc
        except Exception as err:
            if isinstance(cmd,list):
                cmd = " ".join(cmd)
            Error("Pool","run", f"An error occured when calling command {cmd}.\nError: {err}")
    
    def stats(self):
        return self._ps.as_dict()