import sys
import os
import unittest

import asyncio

from peewee import CharField, ForeignKeyField
from fastapi.requests import Request
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.testclient import TestClient

from gws.app import App
from gws.model import Model, Resource, Process, HTMLViewModel, JSONViewModel
from gws.view import HTMLViewTemplate, JSONViewTemplate
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

class HTMLPersonViewModel(HTMLViewModel):
    model_specs = [ Person ]
    template = HTMLViewTemplate("Model={{vmodel.model.id}} & View URI={{vmodel.uri}}: I am <b>{{vmodel.model.name}}</b>! My job is {{vmodel.data.job}}.")

class JSONPersonViewModel(JSONViewModel):
    model_specs = [ Person ]
    template = JSONViewTemplate('{"model_id":"{{vmodel.model.id}}", "view_uri":"{{vmodel.uri}}", "name": "{{vmodel.model.name}}!", "job":"{{vmodel.data.job}}"}')


# ##############################################################################
#
# Testing
#
# ##############################################################################


class TestApp(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        Person.drop_table()
        HTMLPersonViewModel.drop_table()
        JSONPersonViewModel.drop_table()
        pass

    @classmethod
    def tearDownClass(cls):
        Person.drop_table()
        HTMLPersonViewModel.drop_table()
        JSONPersonViewModel.drop_table()
        pass
   
    def test_view(self):
        elon = Person()
        elon_vmodel = HTMLPersonViewModel(model=elon)
        elon.set_name('Elon Musk')
        elon.save()
        elon_vmodel.save()

        pass