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
from gws.controller import Controller


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