# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import sys
import os
import unittest
import asyncio

from peewee import CharField, ForeignKeyField
from fastapi.requests import Request
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.testclient import TestClient

from gws.app import App
from gws.model import Model, Resource, Process, ViewModel

# ##############################################################################
#
# Class definition
#
# ##############################################################################


class Person(Resource):
    @property
    def name(self):
        return self.data['name']
    
    def set_name(self, name):
        self.data['name'] = name

# ##############################################################################
#
# Testing
#
# ##############################################################################


class TestApp(unittest.TestCase):
    pass