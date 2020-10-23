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
    
    @classmethod
    def get_api_url(cls, action):
        settings = Settings.retrieve()
        url = settings.data["central"]["api_url"]
        url = url \
                .replace("{resource}", "lab") \
                .replace("{uri}", Lab.get_uri()) \
                .replace("{action}",action)

        return url

    @classmethod
    def send(cls, url, message={}):
        if Lab.get_uri() == "":
            return False
    
        data = {
            "lab" : Lab.get_status(),
            "message": message
        }
        try:
            response = requests.post(url, data=data)
            return response.status_code == 200
        except:
            return False

    @classmethod
    def send_status(cls, data={}):
        url = cls.get_api_url("update-status")
        cls.send(url)

    @classmethod
    def send_report(cls, report):
        url = cls.get_api_url("add-report")
        cls.send(url, message={"report_uri": report.uri})
    
    @classmethod
    def tell_is_running(cls):
        url = cls.get_api_url("update-status")
        return cls.send(url, message={"status": "on"})
            
    @classmethod
    def tell_is_stopped(cls):
        url = cls.get_api_url("update-status")
        return cls.send(url, message={"status": "off"})