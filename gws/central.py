# LICENSE
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import requests
from gws.settings import Settings
from gws.logger import Logger
from gws.model import Report
from gws.lab import Lab

class Central:
    urls = {
        "status": "lab.api.gws.gencovery.com/status/",
        "report": "lab.api.gws.gencovery.com/report/"
    }
    
    @classmethod
    def send_status(cls, data={}):
        status = Lab.get_status()
        for k in data:
            status[k] = data[k]
        response = requests.post(cls.urls["status"], data=data)
        return response.status_code == 200
    
    @classmethod
    def send_report(cls, report):
        data=Lab.get_status()
        data["report_uri"] = report.uri
        response = requests.post(cls.urls["report"], data=data)
        return response.status_code == 200
    
    @classmethod
    def tell_is_running(cls):
        return cls.send_status({"is_running": True})
    
    @classmethod
    def tell_is_stopped(cls):
        return cls.send_status({"is_running": False})